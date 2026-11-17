"""Generazione del PDF della scheda con la grafica del trainer (ReportLab)."""
import io
import os
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

PAGE_W, PAGE_H = A4
MARGIN = 12 * mm
CONTENT_W = PAGE_W - 2 * MARGIN
HEAD_H = 30 * mm      # intestazione prima pagina
SMALL_HEAD_H = 11 * mm
FOOT_H = 10 * mm
IMG_W, IMG_H = 52 * mm, 39 * mm  # 4:3 come nel programma


def _hex(v, default):
    try:
        return colors.HexColor(v or default)
    except Exception:
        return colors.HexColor(default)


def _t(v):
    return escape(str(v or "")).replace("\n", "<br/>")


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


def _image(path, max_w, max_h):
    """Immagine ridimensionata per stare tutta nel riquadro (senza tagli)."""
    if not path or not os.path.isfile(path) or path.lower().endswith(".svg"):
        return None
    try:
        reader = ImageReader(path)
        iw, ih = reader.getSize()
        k = min(max_w / iw, max_h / ih)
        return Image(path, width=iw * k, height=ih * k)
    except Exception:
        return None


def build_pdf(program, settings, upload_dir, break_days=False):
    brand = _hex(settings.get("primary_color"), "#8c1c3a")
    dark = _hex(settings.get("secondary_color"), "#3a0d1a")
    soft = _hex(settings.get("accent_color"), "#f6e9ed")
    muted = colors.HexColor("#7a6a6f")
    line = colors.HexColor("#e4dade")

    st = {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=dark, spaceAfter=6),
        "label": ParagraphStyle("label", fontName="Helvetica", fontSize=6.5, leading=8, textColor=muted),
        "value": ParagraphStyle("value", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=dark),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#2a1a1f")),
        "day": ParagraphStyle("day", fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=dark),
        "badge": ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=12, leading=14, textColor=colors.white, alignment=TA_CENTER),
        "dnote": ParagraphStyle("dnote", fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=muted),
        "exname": ParagraphStyle("exname", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=dark),
        "chip": ParagraphStyle("chip", fontName="Helvetica-Bold", fontSize=7.5, leading=9, textColor=dark, alignment=TA_RIGHT),
        "link": ParagraphStyle("link", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=brand),
        "num": ParagraphStyle("num", fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=brand, alignment=TA_CENTER),
    }

    # ---------------------------------------------------------- intestazioni
    logo_path = os.path.join(upload_dir, settings["logo"]) if settings.get("logo") else None
    logo = None
    if logo_path and os.path.isfile(logo_path) and not logo_path.lower().endswith(".svg"):
        try:
            logo = ImageReader(logo_path)
        except Exception:
            logo = None
    contacts = [c for c in (settings.get("contact_phone"), settings.get("contact_email"),
                            settings.get("contact_social"), settings.get("website")) if c]

    def footer(c):
        c.setFillColor(dark)
        c.rect(0, 0, PAGE_W, FOOT_H, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(PAGE_W / 2, FOOT_H / 2 - 3, settings.get("footer_text") or "")
        c.setFont("Helvetica", 7.5)
        c.drawRightString(PAGE_W - MARGIN, FOOT_H / 2 - 3, f"{c.getPageNumber()}")

    def first_page(c, _doc):
        c.saveState()
        c.setFillColor(dark)
        c.rect(0, PAGE_H - HEAD_H, PAGE_W, HEAD_H, stroke=0, fill=1)
        c.setFillColor(brand)
        c.rect(0, PAGE_H - HEAD_H - 2 * mm, PAGE_W, 2 * mm, stroke=0, fill=1)
        x = MARGIN
        if logo:
            iw, ih = logo.getSize()
            h = 18 * mm
            w = min(iw * h / ih, 45 * mm)
            h = ih * w / iw
            c.drawImage(logo, x, PAGE_H - HEAD_H / 2 - h / 2, w, h, mask="auto")
            x += w + 5 * mm
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(x, PAGE_H - HEAD_H / 2 + 1 * mm, settings.get("brand_name") or "")
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.Color(1, 1, 1, alpha=0.75))
        c.drawString(x, PAGE_H - HEAD_H / 2 - 5 * mm, (settings.get("brand_subtitle") or "").upper())
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.white)
        y = PAGE_H - HEAD_H / 2 + (len(contacts) - 1) * 2.2 * mm - 1 * mm
        for line_ in contacts:
            c.drawRightString(PAGE_W - MARGIN, y, line_)
            y -= 4.4 * mm
        if settings.get("website"):
            w = c.stringWidth(settings["website"], "Helvetica", 8.5)
            yy = y + 4.4 * mm
            c.linkURL(_url(settings["website"]), (PAGE_W - MARGIN - w, yy - 1, PAGE_W - MARGIN, yy + 8), relative=0)
        footer(c)
        c.restoreState()

    def later_pages(c, _doc):
        c.saveState()
        c.setFillColor(dark)
        c.rect(0, PAGE_H - SMALL_HEAD_H, PAGE_W, SMALL_HEAD_H, stroke=0, fill=1)
        c.setFillColor(brand)
        c.rect(0, PAGE_H - SMALL_HEAD_H - 1.2 * mm, PAGE_W, 1.2 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(MARGIN, PAGE_H - SMALL_HEAD_H / 2 - 3.5, settings.get("brand_name") or "")
        c.setFont("Helvetica", 8.5)
        right = program.get("title") or ""
        if program.get("athlete_name"):
            right += "  ·  " + program["athlete_name"]
        c.drawRightString(PAGE_W - MARGIN, PAGE_H - SMALL_HEAD_H / 2 - 3, right)
        footer(c)
        c.restoreState()

    # ---------------------------------------------------------- contenuto
    story = [Paragraph(_t(program.get("title")), st["title"])]

    info = [(k, v) for k, v in (
        ("ATLETA", program.get("athlete_name")),
        ("OBIETTIVO", program.get("goal")),
        ("INIZIO", _fmt_date(program.get("start_date"))),
        ("FINE", _fmt_date(program.get("end_date"))),
        ("GIORNI", str(len(program["days"]))),
    ) if v]
    if info:
        cells = [[Paragraph(k, st["label"]), Paragraph(_t(v), st["value"])] for k, v in info]
        gap = 2 * mm
        cw = (CONTENT_W - gap * (len(cells) - 1)) / len(cells)
        row, widths = [], []
        for i, cell in enumerate(cells):
            row.append(cell)
            widths.append(cw)
            if i < len(cells) - 1:
                row.append("")
                widths.append(gap)
        t = Table([row], colWidths=widths)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
        for i in range(0, len(row), 2):
            style.append(("BACKGROUND", (i, 0), (i, 0), soft))
        t.setStyle(TableStyle(style))
        story.append(t)

    if program.get("notes"):
        story.append(Spacer(1, 4 * mm))
        nt = Table([["", Paragraph(_t(program["notes"]), st["body"])]], colWidths=[1.3 * mm, CONTENT_W - 1.3 * mm])
        nt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), brand),
            ("BACKGROUND", (1, 0), (1, 0), soft),
            ("LEFTPADDING", (1, 0), (1, 0), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(nt)

    for di, day in enumerate(program["days"]):
        if break_days and di > 0:
            story.append(PageBreak())
        else:
            story.append(Spacer(1, 7 * mm))

        head = Table([[Paragraph(str(di + 1), st["badge"]), Paragraph(_t(day.get("name")), st["day"])]],
                     colWidths=[9 * mm, CONTENT_W - 9 * mm], rowHeights=[9 * mm])
        head.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), brand),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (1, 0), (1, 0), 8),
            ("LINEBELOW", (0, 0), (-1, 0), 1.5, soft),
        ]))
        block = [head, Spacer(1, 2 * mm)]
        if day.get("notes"):
            block += [Paragraph(_t(day["notes"]), st["dnote"]), Spacer(1, 2 * mm)]

        if not day["exercises"]:
            block.append(Paragraph("Nessun esercizio.", st["dnote"]))
        exercise_flows = []
        for ei, ex in enumerate(day["exercises"]):
            exercise_flows.append(_exercise(ex, ei, st, upload_dir, brand, dark, soft, line))
            exercise_flows.append(Spacer(1, 2.5 * mm))
        # se non c'è spazio per intestazione + primo esercizio, si va a pagina nuova
        story.append(CondPageBreak(IMG_H + 32 * mm))
        story.extend(block + exercise_flows)

    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=HEAD_H + 8 * mm, bottomMargin=FOOT_H + 6 * mm,
        title=program.get("title") or "Scheda", author=settings.get("brand_name") or "",
    )
    # dalle pagine successive l'intestazione è più bassa
    first = PageTemplate(id="first", onPage=first_page, frames=[
        Frame(MARGIN, FOOT_H + 6 * mm, CONTENT_W, PAGE_H - HEAD_H - 8 * mm - FOOT_H - 6 * mm, id="f1")])
    later = PageTemplate(id="later", onPage=later_pages, frames=[
        Frame(MARGIN, FOOT_H + 6 * mm, CONTENT_W, PAGE_H - SMALL_HEAD_H - 7 * mm - FOOT_H - 6 * mm, id="f2")])
    first.autoNextPageTemplate = "later"
    later.autoNextPageTemplate = "later"
    doc.addPageTemplates([first, later])
    doc.build(story)
    return buf.getvalue()


def _exercise(ex, index, st, upload_dir, brand, dark, soft, line):
    link = _url(ex.get("link"))
    pic = _image(os.path.join(upload_dir, ex["image"]) if ex.get("image") else None, IMG_W, IMG_H)
    if pic is None:
        pic = Paragraph(str(index + 1), st["num"])

    name = _t(ex.get("name"))
    if link:
        name = f'<link href="{escape(link)}" color="{dark.hexval().replace("0x", "#")}">{name}</link>' \
               f' <font color="{brand.hexval().replace("0x", "#")}">&#187;</font>'
    title = Table([[Paragraph(name, st["exname"]), Paragraph(_t(ex.get("muscle_group")).upper(), st["chip"])]],
                  colWidths=[None, 30 * mm])
    title.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))

    params = [(k, ex.get(f)) for k, f in (("SERIE", "sets"), ("RIPETIZIONI", "reps"), ("RECUPERO", "rest"),
                                          ("CARICO", "load"), ("TUT", "tempo")) if ex.get(f)]
    right = [title, Spacer(1, 2 * mm)]
    if params:
        row, widths = [], []
        for i, (k, v) in enumerate(params):
            row.append([Paragraph(k, st["label"]), Paragraph(_t(v), st["value"])])
            widths.append(21 * mm)
            if i < len(params) - 1:
                row.append("")
                widths.append(1.5 * mm)
        pt = Table([row], colWidths=widths, hAlign="LEFT")
        style = [("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                 ("LEFTPADDING", (0, 0), (-1, -1), 5)]
        for i in range(0, len(row), 2):
            style.append(("BOX", (i, 0), (i, 0), 1.2, soft))
        pt.setStyle(TableStyle(style))
        right += [pt, Spacer(1, 2 * mm)]
    if ex.get("notes"):
        right += [Paragraph("<b>Note:</b> " + _t(ex["notes"]), st["body"]), Spacer(1, 1.5 * mm)]
    if link:
        right.append(Paragraph(f'<link href="{escape(link)}">Guarda l\'esecuzione &#187;</link>', st["link"]))

    t = Table([[pic, right]], colWidths=[IMG_W + 4 * mm, CONTENT_W - IMG_W - 4 * mm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, line),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, 0), 6), ("RIGHTPADDING", (0, 0), (0, 0), 4),
        ("LEFTPADDING", (1, 0), (1, 0), 8), ("RIGHTPADDING", (1, 0), (1, 0), 8),
    ]))
    return t
