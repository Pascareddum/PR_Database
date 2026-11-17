"""Generazione del PDF della scheda - replica l'anteprima HTML il più fedelmente possibile.

Architettura: BaseDocTemplate con page templates che disegnano header/footer su canvas,
e un insieme di Flowable custom per i blocchi complessi (info-card, day-banner, exercise).
"""
import io
import math
import os
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, PageBreak,
                                PageTemplate, Paragraph, Spacer)

PAGE_W, PAGE_H = A4
MARGIN_X = 14 * mm            # margine esterno della card .sheet
INNER_PAD_X = 14 * mm         # padding orizzontale dentro la card (sheet-info / sheet-day)
CARD_X = MARGIN_X
CARD_W = PAGE_W - 2 * MARGIN_X
HEAD_H = 46 * mm              # altezza header prima pagina (sheet-head)
SMALL_HEAD_H = 13 * mm
FOOT_H = 20 * mm              # altezza footer gradient
CONTENT_W = CARD_W - 2 * INNER_PAD_X
IMG_W, IMG_H = 56 * mm, 42 * mm  # 4:3 come anteprima


# ===================================================================== utility
def _hex(v, default):
    try:
        return colors.HexColor(v or default)
    except Exception:
        return colors.HexColor(default)


def _mix(c1, c2, t):
    return colors.Color(
        c1.red + (c2.red - c1.red) * t,
        c1.green + (c2.green - c1.green) * t,
        c1.blue + (c2.blue - c1.blue) * t,
    )


def _alpha(c, a):
    return colors.Color(c.red, c.green, c.blue, alpha=a)


def _t(v):
    return escape(str(v or "")).replace("\n", "<br/>")


def _plain(v):
    return str(v or "")


def _url(link):
    link = (link or "").strip()
    if not link:
        return ""
    return link if re.match(r"^https?://", link, re.I) else "https://" + link


def _fmt_date(d):
    if not d:
        return ""
    p = d.split("-")
    return f"{p[2]}/{p[1]}/{p[0]}" if len(p) == 3 else d


def _truncate(text, max_w, font, size):
    if stringWidth(text, font, size) <= max_w:
        return text
    while text and stringWidth(text + "…", font, size) > max_w:
        text = text[:-1]
    return text + "…"


def _wrap_lines(text, max_w, font, size):
    """Wrap very basic per testo semplice (contact right column)."""
    out, line = [], ""
    for word in str(text).split():
        trial = (line + " " + word).strip()
        if stringWidth(trial, font, size) <= max_w:
            line = trial
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out


# ===================================================================== gradient
def _grad_diag(c, x, y, w, h, c1, c2, c3, steps=80):
    """Gradiente diagonale a 3 stop come CSS --grad.
    Implementato come orizzontale (approssimazione: il clip-path cambia l'inclinazione percepita).
    """
    sw = w / steps
    for i in range(steps):
        t = i / (steps - 1)
        col = _mix(c1, c2, t * 2) if t < 0.5 else _mix(c2, c3, (t - 0.5) * 2)
        c.setFillColor(col)
        c.rect(x + i * sw, y, sw + 0.6, h, stroke=0, fill=1)


def _grad_h(c, x, y, w, h, c1, c2, steps=80):
    sw = w / steps
    for i in range(steps):
        t = i / (steps - 1)
        c.setFillColor(_mix(c1, c2, t))
        c.rect(x + i * sw, y, sw + 0.6, h, stroke=0, fill=1)


def _grad_soft_rect(c, x, y, w, h, brand_soft, radius=14, border=None):
    """Riempie un rounded rect con gradiente soft (brand-soft -> bianco), aggiunge bordo opzionale."""
    c.saveState()
    p = c.beginPath()
    _round_path(p, x, y, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)
    _grad_h(c, x, y, w, h, brand_soft, colors.white, steps=40)
    c.restoreState()
    if border:
        c.setStrokeColor(border)
        c.setLineWidth(0.6)
        c.roundRect(x, y, w, h, radius, stroke=1, fill=0)


def _grad_rounded(c, x, y, w, h, c1, c2, c3, radius=16):
    """Rounded rect riempito con gradient diagonale a 3 stop."""
    c.saveState()
    p = c.beginPath()
    _round_path(p, x, y, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)
    _grad_diag(c, x, y, w, h, c1, c2, c3)
    c.restoreState()


def _round_path(p, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    p.moveTo(x + r, y)
    p.lineTo(x + w - r, y)
    p.arcTo(x + w - 2 * r, y, x + w, y + 2 * r, startAng=270, extent=90)
    p.lineTo(x + w, y + h - r)
    p.arcTo(x + w - 2 * r, y + h - 2 * r, x + w, y + h, startAng=0, extent=90)
    p.lineTo(x + r, y + h)
    p.arcTo(x, y + h - 2 * r, x + 2 * r, y + h, startAng=90, extent=90)
    p.lineTo(x, y + r)
    p.arcTo(x, y, x + 2 * r, y + 2 * r, startAng=180, extent=90)
    p.close()


# ================================================================ icone SVG-like
def _icon_phone(c, cx, cy, size, color):
    """Smartphone: rounded rect verticale + speaker in alto + tasto home in basso."""
    c.saveState()
    w = size * 0.52
    h = size * 0.86
    x = cx - w / 2
    y = cy - h / 2
    r = size * 0.1
    # corpo
    c.setFillColor(color)
    c.roundRect(x, y, w, h, r, stroke=0, fill=1)
    # schermo (bucato con colore sfondo = ritaglio visuale)
    # per non dipendere dallo sfondo uso rettangolo con alpha ridotto
    c.setFillColor(_alpha(color, 0.0))  # ritaglio virtuale: skip
    # speaker (barra orizzontale in alto)
    c.setFillColor(_alpha(colors.white, 0.9))
    bar_w = w * 0.35
    bar_h = size * 0.04
    c.rect(cx - bar_w / 2, y + h - size * 0.1, bar_w, bar_h, stroke=0, fill=1)
    # tasto home (cerchio in basso)
    c.circle(cx, y + size * 0.1, size * 0.055, stroke=0, fill=1)
    c.restoreState()


def _icon_mail(c, cx, cy, size, color):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(size * 0.13)
    c.setLineJoin(1)
    w = size * 0.75
    h = size * 0.55
    x = cx - w / 2
    y = cy - h / 2
    c.rect(x, y, w, h, stroke=1, fill=0)
    p = c.beginPath()
    p.moveTo(x, y + h)
    p.lineTo(cx, y + h * 0.4)
    p.lineTo(x + w, y + h)
    c.drawPath(p, stroke=1, fill=0)
    c.restoreState()


def _icon_insta(c, cx, cy, size, color):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(size * 0.12)
    s = size * 0.7
    c.roundRect(cx - s / 2, cy - s / 2, s, s, s * 0.22, stroke=1, fill=0)
    c.circle(cx, cy, s * 0.22, stroke=1, fill=0)
    c.setFillColor(color)
    c.circle(cx + s * 0.28, cy + s * 0.28, s * 0.07, stroke=0, fill=1)
    c.restoreState()


def _icon_globe(c, cx, cy, size, color):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(size * 0.11)
    r = size * 0.38
    c.circle(cx, cy, r, stroke=1, fill=0)
    p = c.beginPath()
    p.moveTo(cx - r, cy)
    p.lineTo(cx + r, cy)
    p.moveTo(cx, cy - r)
    p.lineTo(cx, cy + r)
    c.drawPath(p, stroke=1, fill=0)
    # ellipsi verticale
    c.saveState()
    c.translate(cx, cy)
    c.scale(0.5, 1)
    c.circle(0, 0, r, stroke=1, fill=0)
    c.restoreState()
    c.restoreState()


def _icon_user(c, cx, cy, size, color):
    c.saveState()
    c.setFillColor(color)
    r = size * 0.19
    c.circle(cx, cy + size * 0.15, r, stroke=0, fill=1)
    p = c.beginPath()
    p.moveTo(cx - size * 0.32, cy - size * 0.35)
    p.curveTo(cx - size * 0.32, cy - size * 0.05, cx + size * 0.32, cy - size * 0.05, cx + size * 0.32, cy - size * 0.35)
    p.lineTo(cx - size * 0.32, cy - size * 0.35)
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def _icon_target(c, cx, cy, size, color):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(size * 0.11)
    r = size * 0.38
    c.circle(cx, cy, r, stroke=1, fill=0)
    c.circle(cx, cy, r * 0.55, stroke=1, fill=0)
    c.setFillColor(color)
    c.circle(cx, cy, r * 0.18, stroke=0, fill=1)
    c.restoreState()


def _icon_calendar(c, cx, cy, size, color):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(size * 0.1)
    w = size * 0.7
    h = size * 0.65
    x = cx - w / 2
    y = cy - h / 2
    c.roundRect(x, y, w, h, size * 0.08, stroke=1, fill=0)
    c.line(x, y + h * 0.7, x + w, y + h * 0.7)
    c.line(x + w * 0.28, y + h, x + w * 0.28, y + h * 0.88)
    c.line(x + w * 0.72, y + h, x + w * 0.72, y + h * 0.88)
    c.restoreState()


def _icon_layers(c, cx, cy, size, color):
    """Manubrio (dumbbell): barra orizzontale + 2 pesi quadrati ai lati + anelli esterni."""
    c.saveState()
    c.setFillColor(color)
    s = size * 0.9
    # peso sinistro (grande)
    plate_w = s * 0.18
    plate_h = s * 0.5
    r = s * 0.04
    lx = cx - s / 2
    c.roundRect(lx, cy - plate_h / 2, plate_w, plate_h, r, stroke=0, fill=1)
    # peso destro
    rx = cx + s / 2 - plate_w
    c.roundRect(rx, cy - plate_h / 2, plate_w, plate_h, r, stroke=0, fill=1)
    # ghiera esterna sinistra (piccola)
    ring_w = s * 0.07
    ring_h = s * 0.7
    c.roundRect(lx - ring_w - s * 0.02, cy - ring_h / 2, ring_w, ring_h, r, stroke=0, fill=1)
    # ghiera esterna destra
    c.roundRect(rx + plate_w + s * 0.02, cy - ring_h / 2, ring_w, ring_h, r, stroke=0, fill=1)
    # barra centrale
    bar_h = s * 0.14
    c.rect(lx + plate_w, cy - bar_h / 2, s - 2 * plate_w, bar_h, stroke=0, fill=1)
    c.restoreState()


def _icon_note(c, cx, cy, size, color):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(size * 0.11)
    w, h = size * 0.6, size * 0.75
    x = cx - w / 2
    y = cy - h / 2
    c.rect(x, y, w, h, stroke=1, fill=0)
    for i in range(3):
        yy = y + h - (i + 1) * h * 0.22
        c.line(x + 1, yy, x + w - 1, yy)
    c.restoreState()


def _icon_play(c, cx, cy, size, color):
    c.saveState()
    c.setFillColor(color)
    p = c.beginPath()
    s = size * 0.5
    p.moveTo(cx - s * 0.4, cy + s)
    p.lineTo(cx - s * 0.4, cy - s)
    p.lineTo(cx + s * 0.8, cy)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


# ================================================================== flowables
class SheetBackground(Flowable):
    """Riempie il frame con sfondo bianco (serve a creare l'illusione della card .sheet)."""
    def __init__(self, width, height):
        super().__init__()
        self.w = width
        self.h = height

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        c.setFillColor(colors.white)
        c.rect(0, 0, self.w, self.h, stroke=0, fill=1)


class InfoCards(Flowable):
    """Griglia .info-grid con card .info-card (icona + eyebrow + valore)."""
    def __init__(self, items, width, brand, dark, soft, muted):
        super().__init__()
        self.items = items  # list[(icon_name, label, value)]
        self.w = width
        self.brand = brand
        self.dark = dark
        self.soft = soft
        self.muted = muted
        self.card_h = 14 * mm
        self.gap = 3 * mm
        # layout a righe (wrap)
        self._compute_rows()
        self.h = len(self.rows) * self.card_h + max(0, len(self.rows) - 1) * self.gap

    def _card_width(self, label, value):
        lw = stringWidth(label, "Helvetica-Bold", 6.5)
        vw = stringWidth(_plain(value), "Helvetica-Bold", 10.5)
        text_w = max(lw, vw)
        return 15 * mm + text_w + 6 * mm  # icon + text + padding destro

    def _compute_rows(self):
        rows, row, used = [], [], 0
        for it in self.items:
            cw = max(42 * mm, self._card_width(it[1], it[2]))
            if row and used + cw + self.gap > self.w:
                rows.append(row)
                row, used = [], 0
            row.append((it, cw))
            used += cw + (self.gap if row else 0)
        if row:
            rows.append(row)
        self.rows = rows

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        y = self.h
        for row in self.rows:
            x = 0
            y -= self.card_h
            for (icon_name, label, value), cw in row:
                self._draw_card(c, x, y, cw, self.card_h, icon_name, label, value)
                x += cw + self.gap
            y -= self.gap

    def _draw_card(self, c, x, y, w, h, icon_name, label, value):
        _grad_soft_rect(c, x, y, w, h, self.soft, radius=10, border=_alpha(self.brand, 0.22))
        # icon box
        ib = 10 * mm
        iy = y + (h - ib) / 2
        ix = x + 2 * mm
        _grad_rounded(c, ix, iy, ib, ib, _mix(self.brand, colors.HexColor("#ff5a5f"), 0.18),
                      self.brand, self.dark, radius=2.5 * mm)
        _get_icon(icon_name)(c, ix + ib / 2, iy + ib / 2, ib * 0.55, colors.white)
        # testo
        tx = ix + ib + 3 * mm
        c.setFillColor(self.muted)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(tx, y + h / 2 + 2.3, label.upper())
        c.setFillColor(self.dark)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(tx, y + h / 2 - 3.5 * mm, _truncate(_plain(value), w - (tx - x) - 2 * mm, "Helvetica-Bold", 10.5))


def _get_icon(name):
    return {
        "user": _icon_user, "target": _icon_target, "calendar": _icon_calendar,
        "layers": _icon_layers, "note": _icon_note, "play": _icon_play,
        "phone": _icon_phone, "mail": _icon_mail, "instagram": _icon_insta, "globe": _icon_globe,
    }.get(name, _icon_user)


class SheetNotes(Flowable):
    """Card .sheet-notes con gradient soft + bordo sx brand + icona + testo."""
    def __init__(self, text, width, brand, dark, soft, muted):
        super().__init__()
        self.text = text
        self.w = width
        self.brand = brand
        self.dark = dark
        self.soft = soft
        self.muted = muted
        self.pad = 4 * mm
        self.icon_box = 8 * mm
        self.text_x = self.pad + self.icon_box + 3 * mm
        self._lines = _wrap_lines(text, width - self.text_x - self.pad, "Helvetica", 9)
        self.h = max(14 * mm, self.pad * 2 + len(self._lines) * 12 + 2)

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        _grad_soft_rect(c, 0, 0, self.w, self.h, self.soft, radius=10, border=_alpha(self.brand, 0.12))
        # barra sx brand
        c.setFillColor(self.brand)
        p = c.beginPath()
        _round_path(p, 0, 0, 2 * mm, self.h, 2 * mm)
        c.drawPath(p, stroke=0, fill=1)
        # icona
        _icon_note(c, self.pad + self.icon_box / 2, self.h - self.pad - self.icon_box / 2 + 1,
                   self.icon_box * 0.9, self.brand)
        # testo
        c.setFillColor(colors.HexColor("#2a1a1f"))
        c.setFont("Helvetica", 9)
        y = self.h - self.pad - 10
        for ln in self._lines:
            c.drawString(self.text_x, y, ln)
            y -= 12


class DayBanner(Flowable):
    """Banner giorno .day-banner: gradient rounded + '01' grande + eyebrow + titolo + note."""
    def __init__(self, idx, name, day_notes, width, brand, dark):
        super().__init__()
        self.idx = idx
        self.name = name or ""
        self.day_notes = day_notes or ""
        self.w = width
        self.brand = brand
        self.dark = dark
        self.h = 20 * mm if self.day_notes else 16 * mm

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        light = _mix(self.brand, colors.HexColor("#ff5a5f"), 0.18)
        _grad_rounded(c, 0, 0, self.w, self.h, light, self.brand, self.dark, radius=5 * mm)
        # cerchio decorativo top-right
        c.saveState()
        p = c.beginPath()
        _round_path(p, 0, 0, self.w, self.h, 5 * mm)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillColor(colors.Color(1, 1, 1, alpha=0.16))
        c.circle(self.w - 10 * mm, self.h + 6 * mm, 35 * mm, stroke=0, fill=1)
        c.restoreState()
        # numero grande semi-trasparente destra
        c.setFillColor(colors.Color(1, 1, 1, alpha=0.18))
        c.setFont("Helvetica-Bold", 44)
        num = f"{self.idx:02d}"
        tw = stringWidth(num, "Helvetica-Bold", 44)
        c.drawString(self.w - tw - 10 * mm, self.h / 2 - 7, num)
        # testo
        c.setFillColor(colors.Color(1, 1, 1, alpha=0.78))
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(7 * mm, self.h - 6 * mm, f"GIORNO {self.idx}")
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(7 * mm, self.h - 12 * mm, self.name)
        if self.day_notes:
            c.setFillColor(colors.Color(1, 1, 1, alpha=0.85))
            c.setFont("Helvetica-Oblique", 9)
            note = _truncate(self.day_notes, self.w - 50 * mm, "Helvetica-Oblique", 9)
            c.drawString(7 * mm, self.h - 17 * mm, note)


class ExerciseCard(Flowable):
    """Card esercizio: bordo sx gradient brand→dark, immagine 4:3 + titolo + chip + params + note + link."""
    IMG_W = IMG_W
    IMG_H = IMG_H
    PAD = 4.5 * mm
    GAP = 6 * mm

    def __init__(self, ex, index, width, brand, dark, soft, muted, line, upload_dir):
        super().__init__()
        self.ex = ex
        self.index = index
        self.w = width
        self.brand = brand
        self.dark = dark
        self.soft = soft
        self.muted = muted
        self.line = line
        self.upload_dir = upload_dir

        # misure
        self.img_area_w = self.IMG_W
        self.right_x = self.PAD + self.img_area_w + self.GAP
        self.right_w = width - self.right_x - self.PAD

        # wrap preventivo note
        self._note_lines = []
        if ex.get("notes"):
            self._note_lines = _wrap_lines(ex["notes"], self.right_w - 6 * mm, "Helvetica", 8.5)[:3]

        # calcola altezza componenti (misure in mm * mm)
        self._h_title = 6 * mm
        self._gap_title_params = 3 * mm
        self._h_params = 11 * mm if self._params() else 0
        self._gap_params_notes = 3 * mm if self._note_lines else 0
        self._h_notes = len(self._note_lines) * 11 + 2 if self._note_lines else 0
        self._gap_notes_link = 3 * mm if ex.get("link") else 0
        self._h_link = 7 * mm if ex.get("link") else 0

        content_h = (self._h_title + self._gap_title_params + self._h_params +
                     self._gap_params_notes + self._h_notes + self._gap_notes_link + self._h_link)
        self.h = max(self.PAD * 2 + self.IMG_H, self.PAD * 2 + content_h)

    def _params(self):
        return [(k, self.ex.get(f)) for k, f in (
            ("SERIE", "sets"), ("RIPETIZIONI", "reps"), ("RECUPERO", "rest"),
            ("CARICO", "load"), ("TUT", "tempo")) if self.ex.get(f)]

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        c = self.canv
        # background card
        _grad_soft_rect(c, 0, 0, self.w, self.h, colors.white, radius=4 * mm,
                        border=_alpha(self.brand, 0.14))
        # gradiente barra sinistra verticale
        c.saveState()
        p = c.beginPath()
        _round_path(p, 0, 0, 2 * mm, self.h, 1.5 * mm)
        c.clipPath(p, stroke=0, fill=0)
        # vertical gradient brand → dark
        steps = 40
        sh = self.h / steps
        for i in range(steps):
            t = i / (steps - 1)
            c.setFillColor(_mix(self.brand, self.dark, t))
            c.rect(0, self.h - (i + 1) * sh, 2 * mm, sh + 0.5, stroke=0, fill=1)
        c.restoreState()
        # immagine / placeholder
        self._draw_image(c)
        # testi destra
        self._draw_right(c)

    def _draw_image(self, c):
        iy = self.h - self.PAD - self.IMG_H
        ix = self.PAD + 2 * mm
        # cornice
        c.saveState()
        path = c.beginPath()
        _round_path(path, ix, iy, self.IMG_W, self.IMG_H, 3 * mm)
        c.clipPath(path, stroke=0, fill=0)
        img_path = os.path.join(self.upload_dir, self.ex["image"]) if self.ex.get("image") else None
        if img_path and os.path.isfile(img_path) and not img_path.lower().endswith(".svg"):
            try:
                reader = ImageReader(img_path)
                iw, ih = reader.getSize()
                scale = max(self.IMG_W / iw, self.IMG_H / ih)
                dw = iw * scale
                dh = ih * scale
                c.drawImage(reader, ix + (self.IMG_W - dw) / 2, iy + (self.IMG_H - dh) / 2,
                            dw, dh, mask="auto")
            except Exception:
                self._draw_placeholder(c, ix, iy)
        else:
            self._draw_placeholder(c, ix, iy)
        c.restoreState()
        # bordo sottile
        c.setStrokeColor(self.line)
        c.setLineWidth(0.5)
        c.roundRect(ix, iy, self.IMG_W, self.IMG_H, 3 * mm, stroke=1, fill=0)
        # badge numero esercizio in alto a sinistra
        bx = ix + 3
        by = iy + self.IMG_H - 8 * mm - 3
        self._draw_num_badge(c, bx, by, 8 * mm, str(self.index + 1))

    def _draw_placeholder(self, c, ix, iy):
        _grad_h(c, ix, iy, self.IMG_W, self.IMG_H, _mix(self.brand, colors.white, 0.85), colors.white)
        _icon_layers(c, ix + self.IMG_W / 2, iy + self.IMG_H / 2, 20 * mm, _alpha(self.brand, 0.6))

    def _draw_num_badge(self, c, x, y, size, text):
        r = size / 2
        c.saveState()
        # cerchio bianco bordo
        c.setFillColor(colors.white)
        c.circle(x + r, y + r, r + 0.8, stroke=0, fill=1)
        # cerchio gradient
        p = c.beginPath()
        p.circle(x + r, y + r, r)
        c.clipPath(p, stroke=0, fill=0)
        _grad_diag(c, x, y, size, size, _mix(self.brand, colors.HexColor("#ff5a5f"), 0.2), self.brand, self.dark)
        c.restoreState()
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", size * 0.52)
        tw = stringWidth(text, "Helvetica-Bold", size * 0.52)
        c.drawString(x + r - tw / 2, y + r - size * 0.18, text)

    def _draw_right(self, c):
        x = self.right_x
        w = self.right_w
        link = _url(self.ex.get("link"))
        # cursor parte dal top, scende giù
        top = self.h - self.PAD
        # TITOLO: baseline a top - fontSize*0.8
        title_baseline = top - 4.2 * mm
        name = _plain(self.ex.get("name"))
        c.setFillColor(self.dark)
        c.setFont("Helvetica-Bold", 12.5)
        max_name_w = w - 32 * mm
        name_disp = _truncate(name, max_name_w, "Helvetica-Bold", 12.5)
        c.drawString(x, title_baseline, name_disp)
        if link:
            tw = stringWidth(name_disp, "Helvetica-Bold", 12.5)
            c.setFillColor(self.brand)
            c.drawString(x + tw + 3, title_baseline, "»")
            c.linkURL(link, (x, title_baseline - 2, x + tw, title_baseline + 10),
                      relative=1, thickness=0)
        # CHIP muscle group a destra, allineato con titolo
        muscle = _plain(self.ex.get("muscle_group")).upper()
        if muscle:
            self._draw_chip(c, x + w, title_baseline + 1, muscle)

        cursor = top - self._h_title  # fondo blocco titolo
        # PARAMS
        if self._params():
            cursor -= self._gap_title_params
            self._draw_params(c, x, cursor, w, self._params())
            cursor -= self._h_params
        # NOTES
        if self._note_lines:
            cursor -= self._gap_params_notes
            _icon_note(c, x + 3, cursor - 2.5, 3.5 * mm, self.brand)
            c.setFillColor(colors.HexColor("#4a3a3f"))
            c.setFont("Helvetica", 8.5)
            for i, ln in enumerate(self._note_lines):
                c.drawString(x + 6 * mm, cursor - 4 - i * 11, ln)
            cursor -= self._h_notes
        # LINK pill
        if link:
            cursor -= self._gap_notes_link
            pill_y = cursor - self._h_link
            self._draw_video_pill(c, x, pill_y, link)

    def _draw_params(self, c, x, y, w, params):
        c.saveState()
        pw = 24 * mm
        gap = 2 * mm
        total = len(params) * pw + (len(params) - 1) * gap
        if total > w:
            pw = (w - (len(params) - 1) * gap) / len(params)
        ph = 11 * mm
        for i, (k, v) in enumerate(params):
            px = x + i * (pw + gap)
            _grad_soft_rect(c, px, y - ph, pw, ph, self.soft, radius=3 * mm, border=_alpha(self.brand, 0.12))
            # linea decorativa sotto
            c.saveState()
            path = c.beginPath()
            _round_path(path, px, y - ph, pw, ph, 3 * mm)
            c.clipPath(path, stroke=0, fill=0)
            _grad_h(c, px + 3 * mm, y - ph - 0.5, pw - 6 * mm, 1.5, self.brand, self.dark, steps=30)
            c.restoreState()
            c.setFillColor(self.muted)
            c.setFont("Helvetica-Bold", 6)
            c.drawString(px + 3 * mm, y - 4 * mm, k)
            c.setFillColor(self.dark)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(px + 3 * mm, y - 9 * mm, _truncate(_plain(v), pw - 6 * mm, "Helvetica-Bold", 11))
        c.restoreState()

    def _draw_chip(self, c, x_right, y, text):
        padx = 3 * mm
        c.saveState()
        c.setFont("Helvetica-Bold", 7)
        tw = stringWidth(text, "Helvetica-Bold", 7)
        chip_w = tw + 2 * padx
        chip_h = 5.5 * mm
        cx = x_right - chip_w
        cy = y - 1 * mm
        _grad_soft_rect(c, cx, cy, chip_w, chip_h, self.soft, radius=chip_h / 2,
                        border=_alpha(self.brand, 0.25))
        c.setFillColor(self.brand)
        c.drawString(cx + padx, cy + chip_h / 2 - 2.3, text)
        c.restoreState()

    def _draw_video_pill(self, c, x, y, link):
        c.saveState()
        c.setFont("Helvetica-Bold", 8)
        text = "Guarda l'esecuzione"
        tw = stringWidth(text, "Helvetica-Bold", 8)
        pad_r = 4 * mm
        icon_size = 4.5 * mm
        pill_h = 6.5 * mm
        pill_w = icon_size + 3 * mm + tw + pad_r
        _grad_rounded(c, x, y, pill_w, pill_h,
                      _mix(self.brand, colors.HexColor("#ff5a5f"), 0.2), self.brand, self.dark,
                      radius=pill_h / 2)
        # cerchio background icona
        c.setFillColor(_alpha(colors.white, 0.22))
        c.circle(x + 2 * mm + icon_size / 2, y + pill_h / 2, icon_size / 2, stroke=0, fill=1)
        _icon_play(c, x + 2 * mm + icon_size / 2, y + pill_h / 2, icon_size * 0.6, colors.white)
        c.setFillColor(colors.white)
        c.drawString(x + 2 * mm + icon_size + 3 * mm, y + pill_h / 2 - 2.5, text)
        c.linkURL(link, (x, y, x + pill_w, y + pill_h), relative=1, thickness=0)
        c.restoreState()


# ========================================================================= build
def build_pdf(program, settings, upload_dir, break_days=False):
    brand = _hex(settings.get("primary_color"), "#8c1c3a")
    dark = _hex(settings.get("secondary_color"), "#3a0d1a")
    soft = _hex(settings.get("accent_color"), "#f6e9ed")
    muted = colors.HexColor("#7a6a6f")
    line = colors.HexColor("#e4dade")
    light_brand = _mix(brand, colors.HexColor("#ff5a5f"), 0.18)

    logo_path = os.path.join(upload_dir, settings["logo"]) if settings.get("logo") else None
    logo = None
    if logo_path and os.path.isfile(logo_path) and not logo_path.lower().endswith(".svg"):
        try:
            logo = ImageReader(logo_path)
        except Exception:
            logo = None
    contacts_raw = []
    for icon, val in [("phone", settings.get("contact_phone")),
                      ("mail", settings.get("contact_email")),
                      ("instagram", settings.get("contact_social")),
                      ("globe", settings.get("website"))]:
        if val:
            contacts_raw.append((icon, val))

    # ------------------------------------------------------------- page bg/foot
    def _draw_sheet_bg(c, _doc):
        """Riempie la pagina con lo sfondo chiaro + card .sheet bianca su cui appoggia tutto."""
        c.setFillColor(colors.HexColor("#f6ecee"))  # bg body chiaro
        c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
        # card sheet
        c.setFillColor(colors.white)
        c.rect(CARD_X, 0, CARD_W, PAGE_H, stroke=0, fill=1)

    def _draw_sheet_head(c, draw_logo=True):
        """Testata colorata + clip-path diagonale + decorazioni + brand + contacts."""
        hx, hy, hw, hh = CARD_X, PAGE_H - HEAD_H, CARD_W, HEAD_H
        c.saveState()
        # clip-path polygon(0 0, 100% 0, 100% 78%, 0 100%)
        p = c.beginPath()
        p.moveTo(hx, hy + hh)
        p.lineTo(hx + hw, hy + hh)
        p.lineTo(hx + hw, hy + hh * 0.22)
        p.lineTo(hx, hy)
        p.close()
        c.clipPath(p, stroke=0, fill=0)
        _grad_diag(c, hx, hy, hw, hh, light_brand, brand, dark)
        # deco-1 cerchio grande alto-destra radial semitrasparente
        c.setFillColor(_alpha(colors.white, 0.18))
        c.circle(hx + hw - 24 * mm, hy + hh + 6 * mm, 60 * mm, stroke=0, fill=1)
        # deco-2 anello basso destra
        c.setStrokeColor(_alpha(colors.white, 0.08))
        c.setLineWidth(8)
        c.circle(hx + hw - 90 * mm, hy - 20 * mm, 32 * mm, stroke=1, fill=0)
        # deco-3 banda inclinata chiara sinistra alta
        c.saveState()
        c.translate(hx + 20 * mm, hy + hh - 10 * mm)
        c.rotate(-8)
        c.setFillColor(_alpha(colors.white, 0.08))
        c.rect(-20 * mm, 0, 150 * mm, 12 * mm, stroke=0, fill=1)
        c.restoreState()
        c.restoreState()

        # contenuto head (brand sx, contatti dx) con padding 34/40
        pad_x = 14 * mm
        center_y = hy + hh / 2 + 3 * mm
        bx = hx + pad_x
        if draw_logo and logo:
            iw, ih = logo.getSize()
            tile_h = 24 * mm
            scale = tile_h / ih
            logo_w = iw * scale
            if logo_w > 44 * mm:
                logo_w = 44 * mm
                scale = logo_w / iw
                tile_h = ih * scale
            tile_pad = 2 * mm
            tile_w = logo_w + 2 * tile_pad
            tile_h2 = tile_h + 2 * tile_pad
            # shadow
            c.setFillColor(_alpha(colors.black, 0.18))
            c.roundRect(bx + 1.5, center_y - tile_h2 / 2 - 1.5, tile_w, tile_h2, 3 * mm, stroke=0, fill=1)
            # tile
            c.setFillColor(colors.white)
            c.roundRect(bx, center_y - tile_h2 / 2, tile_w, tile_h2, 3 * mm, stroke=0, fill=1)
            c.drawImage(logo, bx + tile_pad, center_y - tile_h / 2, logo_w, tile_h, mask="auto")
            bx += tile_w + 5 * mm
        # brand name
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(bx, center_y + 3 * mm, settings.get("brand_name") or "")
        # brand sub pill
        sub = (settings.get("brand_subtitle") or "").upper()
        if sub:
            c.setFont("Helvetica-Bold", 6.5)
            sw = stringWidth(sub, "Helvetica-Bold", 6.5)
            pill_w = sw + 10
            pill_h = 5 * mm
            px = bx
            py = center_y - 4.5 * mm
            c.setFillColor(_alpha(colors.white, 0.14))
            c.roundRect(px, py - pill_h + 1, pill_w, pill_h, pill_h / 2, stroke=0, fill=1)
            c.setStrokeColor(_alpha(colors.white, 0.25))
            c.setLineWidth(0.5)
            c.roundRect(px, py - pill_h + 1, pill_w, pill_h, pill_h / 2, stroke=1, fill=0)
            c.setFillColor(_alpha(colors.white, 0.95))
            c.drawString(px + 5, py - 3 * mm, sub)

        # contacts destra
        cx_right = hx + hw - pad_x
        gap = 4.5 * mm
        total_h = max(0, len(contacts_raw) * gap)
        start_y = center_y + total_h / 2 - 2 * mm
        for icon_name, val in contacts_raw:
            val_str = _plain(val)
            size = 5.5 * mm
            txt_w = stringWidth(val_str, "Helvetica", 9)
            # icona cerchio
            icon_cx = cx_right - txt_w - 4 - size / 2
            icon_cy = start_y
            c.setFillColor(_alpha(colors.white, 0.16))
            c.circle(icon_cx, icon_cy, size / 2 + 0.6, stroke=0, fill=1)
            c.setStrokeColor(_alpha(colors.white, 0.35))
            c.setLineWidth(0.4)
            c.circle(icon_cx, icon_cy, size / 2 + 0.6, stroke=1, fill=0)
            _get_icon(icon_name)(c, icon_cx, icon_cy, size * 0.75, colors.white)
            c.setFillColor(colors.white)
            c.setFont("Helvetica", 9)
            c.drawString(cx_right - txt_w, icon_cy - 2.3, val_str)
            start_y -= gap

    def _draw_sheet_foot(c):
        fy = 0
        fx = CARD_X
        fw = CARD_W
        fh = FOOT_H
        c.saveState()
        # clip path triangolo (polygon(0 32%, 100% 0, 100% 100%, 0 100%))
        p = c.beginPath()
        p.moveTo(fx, fy)
        p.lineTo(fx + fw, fy)
        p.lineTo(fx + fw, fy + fh)
        p.lineTo(fx, fy + fh * 0.68)
        p.close()
        c.clipPath(p, stroke=0, fill=0)
        _grad_diag(c, fx, fy, fw, fh, light_brand, brand, dark)
        c.restoreState()
        # motto + brand
        c.setFillColor(colors.white)
        c.setFont("Helvetica-BoldOblique", 10.5)
        c.drawString(fx + 14 * mm, fy + fh / 2 - 4, settings.get("footer_text") or "")
        c.setFont("Helvetica-Bold", 9)
        brand_txt = settings.get("brand_name") or ""
        bw = stringWidth(brand_txt, "Helvetica-Bold", 9)
        c.drawString(fx + fw - 14 * mm - bw, fy + fh / 2 - 4, brand_txt)
        # numero pagina
        c.setFont("Helvetica", 7)
        c.setFillColor(_alpha(colors.white, 0.75))
        c.drawRightString(fx + fw - 14 * mm, fy + 3 * mm, f"Pag. {c.getPageNumber()}")

    def _draw_small_head(c):
        hx, hy, hw, hh = CARD_X, PAGE_H - SMALL_HEAD_H, CARD_W, SMALL_HEAD_H
        _grad_h(c, hx, hy, hw, hh, dark, brand)
        c.setFillColor(brand)
        c.rect(hx, hy - 1 * mm, hw, 1 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(hx + 10 * mm, hy + hh / 2 - 3, settings.get("brand_name") or "")
        c.setFont("Helvetica", 8.5)
        right = program.get("title") or ""
        if program.get("athlete_name"):
            right += "  ·  " + program["athlete_name"]
        c.drawRightString(hx + hw - 10 * mm, hy + hh / 2 - 3, right)

    def first_page(c, doc):
        c.saveState()
        _draw_sheet_bg(c, doc)
        _draw_sheet_head(c, draw_logo=True)
        _draw_sheet_foot(c)
        c.restoreState()

    def later_page(c, doc):
        c.saveState()
        _draw_sheet_bg(c, doc)
        _draw_small_head(c)
        _draw_sheet_foot(c)
        c.restoreState()

    # ------------------------------------------------------------------ content
    styles = {
        "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=8, leading=10,
                                  textColor=brand, spaceAfter=2),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=22, leading=26,
                             textColor=dark, spaceAfter=6),
    }
    story = []
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("SCHEDA DI ALLENAMENTO", styles["eyebrow"]))
    story.append(Paragraph(_t(program.get("title")), styles["h1"]))

    # info items
    info_items = []
    if program.get("athlete_name"):
        info_items.append(("user", "ATLETA", program["athlete_name"]))
    if program.get("goal"):
        info_items.append(("target", "OBIETTIVO", program["goal"]))
    if program.get("start_date") or program.get("end_date"):
        info_items.append(("calendar", "PERIODO",
                           f'{_fmt_date(program.get("start_date")) or "…"} → {_fmt_date(program.get("end_date")) or "…"}'))
    info_items.append(("layers", "GIORNI", str(len(program["days"]))))
    if info_items:
        story.append(InfoCards(info_items, CONTENT_W, brand, dark, soft, muted))
        story.append(Spacer(1, 4 * mm))
    if program.get("notes"):
        story.append(SheetNotes(program["notes"], CONTENT_W, brand, dark, soft, muted))
        story.append(Spacer(1, 2 * mm))

    for di, day in enumerate(program["days"]):
        if break_days and di > 0:
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 6 * mm))
        story.append(CondPageBreak(IMG_H + 30 * mm))
        story.append(DayBanner(di + 1, day.get("name"), day.get("notes"), CONTENT_W, brand, dark))
        story.append(Spacer(1, 3 * mm))
        if not day["exercises"]:
            style_empty = ParagraphStyle("empty", fontName="Helvetica-Oblique", fontSize=9,
                                         textColor=muted, leading=12)
            story.append(Paragraph("Nessun esercizio.", style_empty))
        for ei, ex in enumerate(day["exercises"]):
            story.append(CondPageBreak(IMG_H + 15 * mm))
            story.append(ExerciseCard(ex, ei, CONTENT_W, brand, dark, soft, muted, line, upload_dir))
            story.append(Spacer(1, 3 * mm))

    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=CARD_X + INNER_PAD_X, rightMargin=CARD_X + INNER_PAD_X,
        topMargin=HEAD_H + 4 * mm, bottomMargin=FOOT_H + 6 * mm,
        title=program.get("title") or "Scheda", author=settings.get("brand_name") or "",
    )
    frame_first = Frame(CARD_X + INNER_PAD_X, FOOT_H + 6 * mm, CONTENT_W,
                        PAGE_H - HEAD_H - 4 * mm - FOOT_H - 6 * mm, id="f1",
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_later = Frame(CARD_X + INNER_PAD_X, FOOT_H + 6 * mm, CONTENT_W,
                        PAGE_H - SMALL_HEAD_H - 6 * mm - FOOT_H - 6 * mm, id="f2",
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    first = PageTemplate(id="first", onPage=first_page, frames=[frame_first])
    later = PageTemplate(id="later", onPage=later_page, frames=[frame_later])
    first.autoNextPageTemplate = "later"
    later.autoNextPageTemplate = "later"
    doc.addPageTemplates([first, later])
    doc.build(story)
    return buf.getvalue()
