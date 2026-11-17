/* Le Schede — frontend (vanilla JS, nessuna dipendenza) */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const app = $("#app");

let SETTINGS = {};
let DIRTY = false;
let VERSION_INFO = null;

const FONTS = ["Montserrat", "Poppins", "Oswald", "Bebas Neue", "Roboto", "Lato", "Raleway", "Anton"];

// ------------------------------------------------------------------ icone (SVG, stile unico in tutto il programma)
const ICONS = {
  phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
  instagram: '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.5" cy="6.5" r="0.6" fill="currentColor"/>',
  globe: '<circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
  play: '<polygon points="7 4 20 12 7 20 7 4" fill="currentColor"/>',
  note: '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1" fill="currentColor"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  layers: '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/>',
  dumbbell: '<path d="M6.5 6.5v11M17.5 6.5v11M3.5 9v6M20.5 9v6M6.5 12h11"/>',
  palette: '<circle cx="13.5" cy="6.5" r="1.3" fill="currentColor"/><circle cx="17.5" cy="10.5" r="1.3" fill="currentColor"/><circle cx="8.5" cy="7.5" r="1.3" fill="currentColor"/><circle cx="6.5" cy="12.5" r="1.3" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.65-.75 1.65-1.69 0-.44-.18-.84-.44-1.13-.29-.29-.44-.65-.44-1.13a1.64 1.64 0 0 1 1.67-1.67h2c3.05 0 5.56-2.5 5.56-5.55C21.97 6.01 17.46 2 12 2z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  edit: '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/>',
  back: '<path d="m15 18-6-6 6-6"/>',
  right: '<path d="m9 18 6-6-6-6"/>',
  up: '<path d="m18 15-6-6-6 6"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
  camera: '<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/>',
  image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  expand: '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>',
  fill: '<rect x="3" y="3" width="18" height="18" rx="2"/><rect x="7" y="7" width="10" height="10" rx="1" fill="currentColor"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
  type: '<path d="M4 7V4h16v3M9 20h6M12 4v16"/>',
  idcard: '<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="8" cy="12" r="2.5"/><path d="M14 10h5M14 14h3"/>',
  cake: '<path d="M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8M4 16s.5-1 2-1 2.5 2 4 2 2.5-2 4-2 2.5 2 4 2 2-1 2-1M2 21h20M7 8v3M12 8v3M17 8v3M7 4h.01M12 4h.01M17 4h.01"/>',
};
const icon = (n, cls = "ico") => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n] || ""}</svg>`;

/* Intestazione di pagina nello stesso stile della scheda (gradiente + forme decorative). */
function hero({ eyebrow = "", title = "", sub = "", actions = "", back = "", ic = "", compact = false, titleId = "" }) {
  return `
    <header class="hero${compact ? " compact" : ""}">
      <span class="deco deco-1"></span><span class="deco deco-2"></span><span class="deco deco-3"></span>
      <div class="hero-main">
        ${ic ? `<span class="hero-ico">${icon(ic)}</span>` : ""}
        <div>
          ${back ? `<a href="${back[0]}" class="hero-back">${icon("back")} ${esc(back[1])}</a>` : ""}
          ${eyebrow ? `<span class="hero-eyebrow">${esc(eyebrow)}</span>` : ""}
          <h1 ${titleId ? `id="${titleId}"` : ""}>${esc(title)}</h1>
          ${sub ? `<p>${sub}</p>` : ""}
        </div>
      </div>
      ${actions ? `<div class="head-actions">${actions}</div>` : ""}
    </header>`;
}
const emptyBox = (ic, html) => `<div class="empty"><span class="empty-ico">${icon(ic)}</span><p>${html}</p></div>`;
const initials = n => String(n || "?").trim().split(/\s+/).slice(0, 2).map(w => w[0]).join("").toUpperCase();

// ------------------------------------------------------------------ utility
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function url(link) {
  if (!link) return "";
  const l = String(link).trim();
  return /^https?:\/\//i.test(l) ? l : "https://" + l;
}
function img(name) { return name ? `/uploads/${encodeURIComponent(name)}` : ""; }
function fmtDate(d) {
  if (!d) return "";
  const [y, m, g] = d.split("-");
  return g ? `${g}/${m}/${y}` : d;
}
function fmtRest(v) {
  const s = String(v ?? "").trim();
  if (!s) return "";
  if (/["']$/.test(s)) return s;
  if (/\d\s*$/.test(s)) return s.replace(/\s*$/, '"');
  return s;
}
function toast(msg, isError = false) {
  const t = $("#toast");
  t.innerHTML = `${icon(isError ? "alert" : "check")}<span>${esc(msg)}</span>`;
  t.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.className = "toast"), 2600);
}

async function api(path, opts = {}) {
  const o = { ...opts };
  if (o.body && !(o.body instanceof FormData)) {
    o.headers = { "Content-Type": "application/json" };
    o.body = JSON.stringify(o.body);
  }
  const res = await fetch("/api" + path, o);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Errore " + res.status);
  return data;
}

// ------------------------------------------------------------------ modale
function openModal({ title, body, okLabel = "Salva", onSubmit, onOpen, wide = false }) {
  const dlg = $("#modal");
  $("#modal-title").textContent = title;
  $("#modal-body").innerHTML = body;
  $("#modal-ok").textContent = okLabel;
  $("#modal-ok").hidden = !onSubmit;
  dlg.classList.toggle("wide", wide);
  const form = $("#modal-form");
  form.onsubmit = async e => {
    e.preventDefault();
    if (!onSubmit) return dlg.close();
    try {
      const keep = await onSubmit(form);
      if (keep !== false) dlg.close();
    } catch (err) { toast(err.message, true); }
  };
  $("#modal-cancel").onclick = () => dlg.close();
  $("#modal-x").onclick = () => dlg.close();
  dlg.showModal();
  onOpen && onOpen(dlg);
  const first = $("input, textarea, select", $("#modal-body"));
  first && first.focus();
}
function confirmBox(message) {
  return new Promise(resolve => {
    openModal({
      title: "Conferma", body: `<p>${esc(message)}</p>`, okLabel: "Conferma",
      onSubmit: () => resolve(true),
    });
    $("#modal").addEventListener("close", () => resolve(false), { once: true });
  });
}

// ------------------------------------------------------------------ branding
function fontLink(font) {
  return `https://fonts.googleapis.com/css2?family=${encodeURIComponent(font)}:wght@400;600;800&display=swap`;
}
function applyBranding(s = SETTINGS) {
  const r = document.documentElement.style;
  r.setProperty("--brand", s.primary_color || "#8c1c3a");
  r.setProperty("--brand-dark", s.secondary_color || "#3a0d1a");
  r.setProperty("--brand-soft", s.accent_color || "#f6e9ed");
  r.setProperty("--brand-font", `"${s.font || "Montserrat"}", system-ui, sans-serif`);
  $("#font-link").href = fontLink(s.font || "Montserrat");
  $("#top-name").textContent = s.brand_name || "Le Schede";
  $("#top-logo-wrap").hidden = !s.logo;
  if (s.logo) $("#top-logo").src = img(s.logo);
}
async function loadSettings() {
  SETTINGS = await api("/settings");
  applyBranding();
}

async function renderUpdateCard() {
  const body = document.getElementById("update-body");
  if (!body) return;
  body.innerHTML = `<p>Controllo in corso…</p>`;
  try { VERSION_INFO = await api("/version"); }
  catch (e) { body.innerHTML = `<p>Impossibile contattare GitHub: ${esc(e.message)}</p>`; return; }
  const v = VERSION_INFO;
  if (v?.error) {
    body.innerHTML = `<p><b>Versione attuale:</b> ${esc(v.current)}</p><p class="muted">Impossibile verificare aggiornamenti: ${esc(v.error)}</p>`;
    return;
  }
  const notes = (v.notes || "").trim();
  if (v.update_available) {
    body.innerHTML = `
      <p><b>Versione attuale:</b> ${esc(v.current)} — <b>disponibile:</b> <span style="color:var(--brand)">${esc(v.latest)}</span></p>
      ${notes ? `<details style="margin:8px 0"><summary class="small">Novità</summary><pre style="white-space:pre-wrap;font:inherit;margin:8px 0 0">${esc(notes)}</pre></details>` : ""}
      <div class="form-grid" style="gap:8px;margin-top:8px">
        <button class="btn primary sm" id="btn-update">${icon("download")} Aggiorna ora</button>
        <a class="btn ghost sm" href="${esc(v.html_url)}" target="_blank" rel="noopener">${icon("eye")} Vedi su GitHub</a>
      </div>
      <p class="small muted" style="margin-top:10px">Dopo l'aggiornamento chiudi e riapri il programma.</p>`;
    document.getElementById("btn-update").onclick = installUpdate;
  } else {
    body.innerHTML = `<p><b>Versione attuale:</b> ${esc(v.current)} ${icon("check")} <span class="muted">— sei aggiornato.</span></p>
      <button class="btn ghost sm" id="btn-recheck">${icon("download")} Controlla di nuovo</button>`;
    document.getElementById("btn-recheck").onclick = renderUpdateCard;
  }
}

async function installUpdate() {
  if (!(await confirmBox("Scaricare e installare l'aggiornamento? Il database e le foto NON verranno toccati. A fine installazione dovrai chiudere e riaprire il programma."))) return;
  const btn = document.getElementById("btn-update");
  if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner sm"></span> Installazione…`; }
  try {
    const r = await api("/update", { method: "POST", body: {} });
    openModal({
      title: "Aggiornamento installato",
      body: `<p>Installata versione <b>${esc(r.installed || "nuova")}</b>.</p>
             <p>Chiudi la finestra nera del programma e riapri <code>avvia.command</code> (Mac) o <code>avvia.bat</code> (Windows) per usare la nuova versione.</p>`,
      okLabel: "Ho capito",
      onSubmit: () => true,
    });
    checkVersion();
  } catch (e) {
    toast(e.message, true);
    if (btn) { btn.disabled = false; btn.innerHTML = `${icon("download")} Aggiorna ora`; }
  }
}

async function checkVersion() {
  try {
    VERSION_INFO = await api("/version");
  } catch { VERSION_INFO = null; return; }
  const b = document.getElementById("update-badge");
  if (!b) return;
  if (VERSION_INFO?.pending_restart) {
    b.hidden = false;
    b.textContent = `Riavvia per applicare v${VERSION_INFO.pending_restart}`;
    b.title = `Aggiornamento v${VERSION_INFO.pending_restart} installato. Chiudi e riapri il programma.`;
    b.classList.add("ready");
  } else if (VERSION_INFO?.update_available) {
    b.hidden = false;
    b.textContent = `Aggiornamento v${VERSION_INFO.latest}`;
    b.title = `Versione attuale ${VERSION_INFO.current} — disponibile ${VERSION_INFO.latest}`;
    b.classList.remove("ready");
  } else {
    b.hidden = true;
    b.classList.remove("ready");
  }
}

// ------------------------------------------------------------------ router
const routes = [
  [/^#\/schede$/, renderPrograms],
  [/^#\/scheda\/(\d+)\/modifica$/, renderEditor],
  [/^#\/scheda\/(\d+)$/, renderSheet],
  [/^#\/esercizi$/, renderExercises],
  [/^#\/atleti$/, renderAthletes],
  [/^#\/impostazioni$/, renderSettings],
];
let lastHash = location.hash;
async function router() {
  if (DIRTY && !confirm("Ci sono modifiche non salvate. Uscire comunque?")) {
    history.replaceState(null, "", lastHash);
    return;
  }
  DIRTY = false;
  applyBranding(); // annulla eventuali anteprime non salvate
  document.onkeydown = null;
  const hash = location.hash || "#/schede";
  lastHash = hash;
  $$("[data-nav]").forEach(a => a.classList.toggle("active", hash.startsWith("#/" + a.dataset.nav) ||
    (a.dataset.nav === "schede" && hash.startsWith("#/scheda"))));
  for (const [re, fn] of routes) {
    const m = hash.match(re);
    if (m) {
      app.innerHTML = `<div class="loading"><span class="spinner"></span>Caricamento…</div>`;
      try { await fn(...m.slice(1)); } catch (e) { app.innerHTML = emptyBox("alert", esc(e.message)); }
      window.scrollTo(0, 0);
      return;
    }
  }
  location.hash = "#/schede";
}
window.addEventListener("hashchange", router);
window.addEventListener("beforeunload", e => { if (DIRTY) { e.preventDefault(); e.returnValue = ""; } });

// ================================================================== SCHEDE
async function renderPrograms() {
  const [programs, athletes] = await Promise.all([api("/programs"), api("/athletes")]);
  const params = new URLSearchParams(location.search);
  app.innerHTML = `
    ${hero({
      eyebrow: "Le tue schede", title: "Schede di allenamento", ic: "file",
      sub: `${programs.length} ${programs.length == 1 ? "scheda" : "schede"} · crea e gestisci le schede dei tuoi atleti.`,
      actions: `<button class="btn light" id="new-prg">${icon("plus")} Nuova scheda</button>`,
    })}
    <div class="toolbar">
      <div class="search">${icon("search")}<input type="search" id="prg-search" placeholder="Cerca per titolo o atleta…"></div>
      <select id="prg-athlete"><option value="">Tutti gli atleti</option>
        ${athletes.map(a => `<option value="${a.id}">${esc(a.name)}</option>`).join("")}</select>
    </div>
    <div id="prg-list" class="card-grid"></div>`;
  const filterAth = sessionStorage.getItem("filterAthlete") || params.get("atleta") || "";
  sessionStorage.removeItem("filterAthlete");
  $("#prg-athlete").value = filterAth;

  const draw = () => {
    const q = $("#prg-search").value.toLowerCase();
    const a = $("#prg-athlete").value;
    const list = programs.filter(p =>
      (!a || String(p.athlete_id) === a) &&
      (!q || (p.title + " " + (p.athlete_name || "")).toLowerCase().includes(q)));
    $("#prg-list").innerHTML = list.length ? list.map(p => `
      <article class="card prg-card">
        <a class="prg-top" href="#/scheda/${p.id}">
          <span class="deco deco-1"></span>
          <div class="prg-top-text"><span class="hero-eyebrow">Scheda</span><h3>${esc(p.title)}</h3></div>
          <span class="prg-days"><b>${String(p.days_count).padStart(2, "0")}</b><small>${p.days_count == 1 ? "giorno" : "giorni"}</small></span>
        </a>
        <div class="prg-body">
          <div class="meta"><span class="meta-ico">${icon("user")}</span>${p.athlete_name ? esc(p.athlete_name) : `<em class="muted">Nessun atleta</em>`}</div>
          ${p.goal ? `<div class="meta"><span class="meta-ico">${icon("target")}</span>${esc(p.goal)}</div>` : ""}
          ${p.start_date || p.end_date ? `<div class="meta"><span class="meta-ico">${icon("calendar")}</span>${fmtDate(p.start_date) || "…"} → ${fmtDate(p.end_date) || "…"}</div>` : ""}
          <div class="card-actions">
            <a class="btn primary sm" href="#/scheda/${p.id}">${icon("eye")} Apri</a>
            <a class="btn ghost sm" href="#/scheda/${p.id}/modifica">${icon("edit")} Modifica</a>
            <span class="spacer"></span>
            <button class="btn ghost sm sq" data-dup="${p.id}" title="Duplica">${icon("copy")}</button>
            <button class="btn ghost sm sq danger" data-del="${p.id}" title="Elimina">${icon("trash")}</button>
          </div>
        </div>
      </article>`).join("")
      : emptyBox("file", programs.length ? "Nessun risultato." : "Nessuna scheda. Clicca <b>Nuova scheda</b> per iniziare.");
  };
  draw();
  $("#prg-search").oninput = draw;
  $("#prg-athlete").onchange = draw;

  $("#prg-list").onclick = async e => {
    const dup = e.target.closest("[data-dup]");
    const del = e.target.closest("[data-del]");
    if (dup) {
      const p = await api(`/programs/${dup.dataset.dup}/duplicate`, { method: "POST" });
      toast("Scheda duplicata");
      location.hash = `#/scheda/${p.id}/modifica`;
    }
    if (del && await confirmBox("Eliminare definitivamente questa scheda?")) {
      await api(`/programs/${del.dataset.del}`, { method: "DELETE" });
      toast("Scheda eliminata");
      renderPrograms();
    }
  };

  $("#new-prg").onclick = () => openModal({
    title: "Nuova scheda",
    okLabel: "Crea",
    body: `
      <label>Titolo<input name="title" required placeholder="Es. Ipertrofia – Mesociclo 1"></label>
      <label>Atleta<select name="athlete_id"><option value="">— nessuno —</option>
        ${athletes.map(a => `<option value="${a.id}">${esc(a.name)}</option>`).join("")}</select></label>
      <label>Numero di giorni di allenamento<input name="ndays" type="number" min="0" max="14" value="3"></label>`,
    onSubmit: async f => {
      const n = +f.ndays.value || 0;
      const days = Array.from({ length: n }, (_, i) => ({ name: `Giorno ${String.fromCharCode(65 + i)}`, exercises: [] }));
      const p = await api("/programs", { method: "POST", body: { title: f.title.value, athlete_id: f.athlete_id.value, days } });
      location.hash = `#/scheda/${p.id}/modifica`;
    },
  });
}

// ================================================================== EDITOR
async function renderEditor(id) {
  const [prog, athletes, exercises] = await Promise.all([api(`/programs/${id}`), api("/athletes"), api("/exercises")]);
  const exById = Object.fromEntries(exercises.map(e => [e.id, e]));
  const state = prog; // modificato in memoria, salvato con PUT

  app.innerHTML = `
    ${hero({
      compact: true, back: ["#/schede", "Schede"], eyebrow: "Modifica scheda", title: state.title, titleId: "ed-title",
      actions: `<a class="btn glass" href="#/scheda/${id}">${icon("eye")} Anteprima</a>
                <button class="btn light" id="save">${icon("save")} Salva</button>`,
    })}

    <section class="card">
      <div class="section-title"><span class="info-ico">${icon("file")}</span><h3>Dati della scheda</h3></div>
      <div class="form-grid">
        <label class="span2">Titolo scheda<input id="f-title" value="${esc(state.title)}"></label>
        <label>Atleta<select id="f-athlete"><option value="">— nessuno —</option>
          ${athletes.map(a => `<option value="${a.id}" ${a.id == state.athlete_id ? "selected" : ""}>${esc(a.name)}</option>`).join("")}
        </select></label>
        <label>Obiettivo<input id="f-goal" value="${esc(state.goal)}" placeholder="Es. Forza, dimagrimento…"></label>
        <label>Data inizio<input type="date" id="f-start" value="${esc(state.start_date)}"></label>
        <label>Data fine<input type="date" id="f-end" value="${esc(state.end_date)}"></label>
        <label class="span2">Note generali<textarea id="f-notes" rows="2" placeholder="Indicazioni generali, riscaldamento, alimentazione…">${esc(state.notes)}</textarea></label>
      </div>
    </section>

    <div id="days"></div>
    <button class="btn dashed block" id="add-day">${icon("plus")} Aggiungi giorno di allenamento</button>
  `;

  const markDirty = () => { DIRTY = true; $("#save").classList.add("pulse"); };
  const bind = (sel, key) => $(sel).addEventListener("input", e => { state[key] = e.target.value; markDirty(); });
  bind("#f-title", "title"); bind("#f-goal", "goal"); bind("#f-start", "start_date");
  bind("#f-end", "end_date"); bind("#f-notes", "notes"); bind("#f-athlete", "athlete_id");
  $("#f-title").addEventListener("input", e => ($("#ed-title").textContent = e.target.value));

  const move = (arr, i, d) => { const j = i + d; if (j < 0 || j >= arr.length) return; [arr[i], arr[j]] = [arr[j], arr[i]]; };

  function drawDays() {
    $("#days").innerHTML = state.days.map((day, di) => `
      <section class="card day" data-di="${di}">
        <div class="day-head">
          <span class="day-num">${String(di + 1).padStart(2, "0")}</span>
          <div class="day-head-text">
            <span class="day-eyebrow">Giorno ${di + 1}</span>
            <input class="day-name" data-k="name" value="${esc(day.name)}" placeholder="Nome giorno (es. Push, Gambe…)">
          </div>
          <div class="icon-btns">
            <button class="icon" data-act="day-up" title="Sposta su">${icon("up")}</button>
            <button class="icon" data-act="day-down" title="Sposta giù">${icon("down")}</button>
            <button class="icon" data-act="day-dup" title="Duplica giorno">${icon("copy")}</button>
            <button class="icon danger" data-act="day-del" title="Elimina giorno">${icon("trash")}</button>
          </div>
        </div>
        <div class="day-body">
        <div class="day-notes-wrap">${icon("note")}<input class="day-notes" data-k="notes" value="${esc(day.notes)}" placeholder="Note del giorno (facoltative)"></div>
        <div class="ex-rows">
          ${day.exercises.length ? `
          <div class="ex-row ex-row-head">
            <span></span><span>Esercizio</span><span>Serie</span><span>Ripetizioni</span><span>Recupero</span><span>Carico</span><span>TUT</span><span>Note</span><span></span>
          </div>` : `<p class="muted small center">Nessun esercizio in questo giorno.</p>`}
          ${day.exercises.map((ex, ei) => {
            const info = exById[ex.exercise_id] || ex;
            return `
            <div class="ex-row" data-ei="${ei}">
              <div class="thumb">${info.image ? `<img src="${img(info.image)}" alt="">` : icon("dumbbell")}<span class="thumb-num">${ei + 1}</span></div>
              <div class="ex-name"><b>${esc(info.name)}</b>${info.muscle_group ? `<span class="chip">${esc(info.muscle_group)}</span>` : ""}</div>
              <input data-f="sets" value="${esc(ex.sets)}" placeholder="4" aria-label="Serie">
              <input data-f="reps" value="${esc(ex.reps)}" placeholder="8-10" aria-label="Ripetizioni">
              <input data-f="rest" value="${esc(ex.rest)}" placeholder='90&quot;' aria-label="Recupero (secondi)">
              <input data-f="load" value="${esc(ex.load)}" placeholder="70% / 40kg" aria-label="Carico">
              <input data-f="tempo" value="${esc(ex.tempo)}" placeholder="3-1-1" aria-label="Tempo">
              <input data-f="notes" value="${esc(ex.notes)}" placeholder="Note" aria-label="Note">
              <div class="icon-btns">
                <button class="icon" data-act="ex-up" title="Su">${icon("up")}</button>
                <button class="icon" data-act="ex-down" title="Giù">${icon("down")}</button>
                <button class="icon danger" data-act="ex-del" title="Rimuovi">${icon("x")}</button>
              </div>
            </div>`;
          }).join("")}
        </div>
        <button class="btn ghost sm" data-act="ex-add">${icon("plus")} Aggiungi esercizi</button>
        </div>
      </section>`).join("") || emptyBox("layers", "Nessun giorno di allenamento. Aggiungine uno qui sotto.");
  }
  drawDays();

  $("#days").addEventListener("input", e => {
    const dayEl = e.target.closest(".day");
    if (!dayEl) return;
    const day = state.days[dayEl.dataset.di];
    if (e.target.dataset.k) day[e.target.dataset.k] = e.target.value;
    const row = e.target.closest(".ex-row[data-ei]");
    if (row && e.target.dataset.f) day.exercises[row.dataset.ei][e.target.dataset.f] = e.target.value;
    markDirty();
  });
  $("#days").addEventListener("blur", e => {
    if (e.target.dataset?.f !== "rest") return;
    const row = e.target.closest(".ex-row[data-ei]");
    const dayEl = e.target.closest(".day");
    if (!row || !dayEl) return;
    const v = fmtRest(e.target.value);
    e.target.value = v;
    state.days[dayEl.dataset.di].exercises[row.dataset.ei].rest = v;
  }, true);

  $("#days").addEventListener("click", async e => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const di = +btn.closest(".day").dataset.di;
    const day = state.days[di];
    const row = btn.closest(".ex-row[data-ei]");
    const ei = row ? +row.dataset.ei : -1;
    switch (btn.dataset.act) {
      case "day-up": move(state.days, di, -1); break;
      case "day-down": move(state.days, di, 1); break;
      case "day-dup": state.days.splice(di + 1, 0, JSON.parse(JSON.stringify({ ...day, name: day.name + " (copia)" }))); break;
      case "day-del":
        if (day.exercises.length && !(await confirmBox(`Eliminare "${day.name}" e i suoi esercizi?`))) return;
        state.days.splice(di, 1); break;
      case "ex-up": move(day.exercises, ei, -1); break;
      case "ex-down": move(day.exercises, ei, 1); break;
      case "ex-del": day.exercises.splice(ei, 1); break;
      case "ex-add": return pickExercises(exercises, picked => {
        picked.forEach(x => day.exercises.push({
          exercise_id: x.id, sets: x.default_sets || "", reps: x.default_reps || "", rest: x.default_rest || "",
          load: "", tempo: "", notes: "",
        }));
        markDirty(); drawDays();
      });
    }
    markDirty(); drawDays();
  });

  $("#add-day").onclick = () => {
    state.days.push({ name: `Giorno ${String.fromCharCode(65 + state.days.length)}`, notes: "", exercises: [] });
    markDirty(); drawDays();
    $$(".day-name").at(-1).focus();
  };

  const save = async () => {
    try {
      const saved = await api(`/programs/${id}`, { method: "PUT", body: state });
      Object.assign(state, saved);
      DIRTY = false;
      $("#save").classList.remove("pulse");
      toast("Scheda salvata");
    } catch (err) { toast(err.message, true); }
  };
  $("#save").onclick = save;
  document.onkeydown = e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s" && location.hash.endsWith("/modifica")) { e.preventDefault(); save(); }
  };
}

function pickExercises(exercises, onPick) {
  if (!exercises.length) {
    return openModal({ title: "Libreria vuota", body: `<p>Non hai ancora esercizi in libreria.<br><a href="#/esercizi" onclick="document.getElementById('modal').close()">Vai a Esercizi</a> per aggiungerli.</p>` });
  }
  const selected = new Set();
  const groups = [...new Set(exercises.map(e => e.muscle_group).filter(Boolean))].sort();
  openModal({
    title: "Scegli esercizi",
    wide: true,
    okLabel: "Aggiungi selezionati",
    body: `
      <div class="toolbar">
        <div class="search">${icon("search")}<input type="search" id="pk-q" placeholder="Cerca esercizio…"></div>
        <select id="pk-g"><option value="">Tutti i gruppi</option>${groups.map(g => `<option>${esc(g)}</option>`).join("")}</select>
      </div>
      <div id="pk-list" class="pick-grid"></div>
      <p class="small muted" id="pk-count">Clicca per selezionare (anche più di uno).</p>`,
    onOpen: () => {
      const draw = () => {
        const q = $("#pk-q").value.toLowerCase(), g = $("#pk-g").value;
        $("#pk-list").innerHTML = exercises
          .filter(e => (!g || e.muscle_group === g) && (!q || (e.name + " " + (e.equipment || "")).toLowerCase().includes(q)))
          .map(e => `
            <button type="button" class="pick ${selected.has(e.id) ? "sel" : ""}" data-id="${e.id}">
              <div class="pick-img">${e.image ? `<img src="${img(e.image)}" alt="">` : icon("dumbbell")}<span class="pick-check">${icon("check")}</span></div>
              <b>${esc(e.name)}</b>${e.muscle_group ? `<span class="chip">${esc(e.muscle_group)}</span>` : ""}
            </button>`).join("") || `<p class="muted">Nessun risultato.</p>`;
      };
      draw();
      $("#pk-q").oninput = draw; $("#pk-g").onchange = draw;
      $("#pk-list").onclick = e => {
        const b = e.target.closest(".pick"); if (!b) return;
        const id = +b.dataset.id;
        selected.has(id) ? selected.delete(id) : selected.add(id);
        b.classList.toggle("sel");
        $("#pk-count").textContent = `${selected.size} selezionati`;
      };
    },
    onSubmit: () => onPick(exercises.filter(e => selected.has(e.id))),
  });
}

// ================================================================== SCHEDA (vista/stampa)
function instaUrl(v) {
  const s = String(v || "").trim();
  if (/^https?:\/\//i.test(s) || s.includes(".")) return url(s);
  return "https://instagram.com/" + s.replace(/^@/, "");
}

async function renderSheet(id) {
  const p = await api(`/programs/${id}`);
  const s = SETTINGS;
  const contacts = [
    s.contact_phone && `<a class="contact" href="tel:${esc(s.contact_phone.replace(/\s+/g, ""))}"><span class="c-ico">${icon("phone")}</span>${esc(s.contact_phone)}</a>`,
    s.contact_email && `<a class="contact" href="mailto:${esc(s.contact_email)}"><span class="c-ico">${icon("mail")}</span>${esc(s.contact_email)}</a>`,
    s.contact_social && `<a class="contact" href="${esc(instaUrl(s.contact_social))}" target="_blank" rel="noopener"><span class="c-ico">${icon("instagram")}</span>${esc(s.contact_social)}</a>`,
    s.website && `<a class="contact" href="${esc(url(s.website))}" target="_blank" rel="noopener"><span class="c-ico">${icon("globe")}</span>${esc(s.website)}</a>`,
  ].filter(Boolean);
  const info = [
    p.athlete_name && ["user", "Atleta", esc(p.athlete_name)],
    p.goal && ["target", "Obiettivo", esc(p.goal)],
    (p.start_date || p.end_date) && ["calendar", "Periodo", `${fmtDate(p.start_date) || "…"} → ${fmtDate(p.end_date) || "…"}`],
    ["layers", "Giorni", p.days.length],
  ].filter(Boolean);
  const two = n => String(n).padStart(2, "0");

  app.innerHTML = `
    <div class="sheet-toolbar no-print">
      <a href="#/schede" class="btn ghost">${icon("back")} Schede</a>
      <div class="head-actions">
        <a class="btn ghost" href="#/scheda/${id}/modifica">${icon("edit")} Modifica</a>
        <button class="btn primary" id="save-pdf">${icon("download")} Salva PDF</button>
      </div>
    </div>

    <article class="sheet" id="sheet">
      <header class="sheet-head">
        <span class="deco deco-1"></span><span class="deco deco-2"></span><span class="deco deco-3"></span>
        <div class="sheet-brand">
          ${s.logo ? `<div class="logo-tile"><img src="${img(s.logo)}" alt=""></div>` : ""}
          <div>
            <div class="sheet-brand-name">${esc(s.brand_name)}</div>
            <div class="sheet-brand-sub">${esc(s.brand_subtitle)}</div>
          </div>
        </div>
        ${contacts.length ? `<div class="sheet-contacts">${contacts.join("")}</div>` : ""}
      </header>

      <section class="sheet-info">
        <div class="eyebrow">Scheda di allenamento</div>
        <h1>${esc(p.title)}</h1>
        <div class="info-grid">
          ${info.map(([ic, k, v]) => `<div class="info-card"><span class="info-ico">${icon(ic)}</span><div><span>${k}</span><b>${v}</b></div></div>`).join("")}
        </div>
        ${p.notes ? `<div class="sheet-notes"><span class="info-ico">${icon("note")}</span><p>${esc(p.notes).replace(/\n/g, "<br>")}</p></div>` : ""}
      </section>

      ${p.days.map((d, i) => `
        <section class="sheet-day">
          <div class="day-banner">
            <div><span class="day-eyebrow">Giorno ${i + 1}</span><h2>${esc(d.name)}</h2>
              ${d.notes ? `<p class="day-note">${esc(d.notes)}</p>` : ""}</div>
            <span class="day-big">${two(i + 1)}</span>
          </div>
          <div class="sheet-ex-list">
          ${d.exercises.map((e, j) => `
            <div class="sheet-ex">
              <div class="sheet-ex-img">
                ${e.image ? `<img src="${img(e.image)}" alt="${esc(e.name)}">` : `<span class="no-img">${icon("layers")}</span>`}
                <span class="ex-num">${j + 1}</span>
              </div>
              <div class="sheet-ex-body">
                <div class="sheet-ex-title">
                  <h3>${e.link ? `<a href="${esc(url(e.link))}" target="_blank" rel="noopener">${esc(e.name)}</a>` : esc(e.name)}</h3>
                  ${e.muscle_group ? `<span class="chip">${esc(e.muscle_group)}</span>` : ""}
                </div>
                <div class="sheet-params">
                  ${e.sets ? `<div><span>Serie</span><b>${esc(e.sets)}</b></div>` : ""}
                  ${e.reps ? `<div><span>Ripetizioni</span><b>${esc(e.reps)}</b></div>` : ""}
                  ${e.rest ? `<div><span>Recupero</span><b>${esc(e.rest)}</b></div>` : ""}
                  ${e.load ? `<div><span>Carico</span><b>${esc(e.load)}</b></div>` : ""}
                  ${e.tempo ? `<div><span>TUT</span><b>${esc(e.tempo)}</b></div>` : ""}
                </div>
                ${e.notes ? `<p class="sheet-ex-notes">${icon("note")}<span>${esc(e.notes)}</span></p>` : ""}
                ${e.link ? `<a class="sheet-video" href="${esc(url(e.link))}" target="_blank" rel="noopener">${icon("play")} Guarda l'esecuzione</a>` : ""}
              </div>
            </div>`).join("") || `<p class="muted">Nessun esercizio.</p>`}
          </div>
        </section>`).join("")}

      <footer class="sheet-foot">
        <span class="foot-motto">${esc(s.footer_text)}</span>
        <span class="foot-brand">${esc(s.brand_name)}</span>
      </footer>
    </article>`;

  $("#sheet").classList.add("break-days");
  $("#save-pdf").onclick = () => savePdf(p);
}

async function savePdf(p) {
  const fileName = ["Scheda", p.title, p.athlete_name].filter(Boolean).join(" - ").replace(/[\\/:*?"<>|]+/g, "").trim() + ".pdf";
  const pdfUrl = `/api/programs/${p.id}/pdf`;
  const btn = $("#save-pdf");
  // Edge/Chrome: finestra "Salva con nome" per scegliere cartella e nome del file
  if (window.showSaveFilePicker) {
    let handle;
    try {
      handle = await window.showSaveFilePicker({
        suggestedName: fileName,
        types: [{ description: "Documento PDF", accept: { "application/pdf": [".pdf"] } }],
      });
    } catch (e) {
      if (e.name === "AbortError") return; // annullato dall'utente
      handle = null;
    }
    if (handle) {
      btn.disabled = true; btn.innerHTML = `<span class="spinner sm"></span> Creazione PDF…`;
      try {
        const res = await fetch(pdfUrl);
        if (!res.ok) throw new Error("Errore nella creazione del PDF");
        const w = await handle.createWritable();
        await w.write(await res.blob());
        await w.close();
        toast("PDF salvato");
      } catch (e) { toast(e.message, true); }
      finally { btn.disabled = false; btn.innerHTML = `${icon("download")} Salva PDF`; }
      return;
    }
  }
  // altri browser: download diretto nella cartella Download
  const a = document.createElement("a");
  a.href = pdfUrl; a.download = fileName;
  document.body.appendChild(a); a.click(); a.remove();
  toast("PDF scaricato nella cartella Download");
}

// ================================================================== ESERCIZI
async function renderExercises() {
  const list = await api("/exercises");
  const groups = [...new Set(list.map(e => e.muscle_group).filter(Boolean))].sort();
  app.innerHTML = `
    ${hero({
      eyebrow: "Libreria", title: "Esercizi", ic: "dumbbell",
      sub: `${list.length} esercizi nel database · aggiungili una volta, usali in tutte le schede.`,
      actions: `<button class="btn light" id="new-ex">${icon("plus")} Nuovo esercizio</button>`,
    })}
    <div class="toolbar">
      <div class="search">${icon("search")}<input type="search" id="ex-q" placeholder="Cerca per nome o attrezzo…"></div>
      <select id="ex-g"><option value="">Tutti i gruppi muscolari</option>${groups.map(g => `<option>${esc(g)}</option>`).join("")}</select>
    </div>
    <div id="ex-list" class="card-grid ex-grid"></div>
    <datalist id="dl-groups">${groups.map(g => `<option value="${esc(g)}">`).join("")}</datalist>`;

  const draw = () => {
    const q = $("#ex-q").value.toLowerCase(), g = $("#ex-g").value;
    const f = list.filter(e => (!g || e.muscle_group === g) && (!q || (e.name + " " + (e.equipment || "")).toLowerCase().includes(q)));
    $("#ex-list").innerHTML = f.length ? f.map(e => `
      <article class="card ex-card">
        <div class="ex-img">
          ${e.image ? `<img src="${img(e.image)}" alt="">` : `<span class="no-img">${icon("dumbbell")}</span>`}
          ${e.muscle_group ? `<span class="chip ex-img-chip">${esc(e.muscle_group)}</span>` : ""}
        </div>
        <div class="ex-card-body">
          <h3>${esc(e.name)}</h3>
          ${e.equipment ? `<div class="meta small"><span class="meta-ico">${icon("dumbbell")}</span>${esc(e.equipment)}</div>` : ""}
          ${e.default_sets || e.default_reps || e.default_rest ? `<div class="sheet-params mini">
            ${e.default_sets ? `<div><span>Serie</span><b>${esc(e.default_sets)}</b></div>` : ""}
            ${e.default_reps ? `<div><span>Rip.</span><b>${esc(e.default_reps)}</b></div>` : ""}
            ${e.default_rest ? `<div><span>Recupero</span><b>${esc(e.default_rest)}</b></div>` : ""}</div>` : ""}
          ${e.link ? `<a class="sheet-video sm" href="${esc(url(e.link))}" target="_blank" rel="noopener">${icon("play")} Esecuzione</a>` : ""}
          <div class="card-actions">
            <button class="btn ghost sm" data-edit="${e.id}">${icon("edit")} Modifica</button>
            <button class="btn ghost sm sq danger" data-del="${e.id}" title="Elimina">${icon("trash")}</button>
            <span class="spacer"></span>
            ${e.usage ? `<span class="usage" title="Schede che usano questo esercizio">${icon("file")} in ${e.usage} ${e.usage == 1 ? "scheda" : "schede"}</span>` : ""}
          </div>
        </div>
      </article>`).join("")
      : emptyBox("dumbbell", list.length ? "Nessun risultato." : "La libreria è vuota. Aggiungi il tuo primo esercizio!");
  };
  draw();
  $("#ex-q").oninput = draw; $("#ex-g").onchange = draw;

  $("#new-ex").onclick = () => exerciseForm();
  $("#ex-list").onclick = async e => {
    const ed = e.target.closest("[data-edit]"), del = e.target.closest("[data-del]");
    if (ed) exerciseForm(list.find(x => x.id == ed.dataset.edit));
    if (del && await confirmBox("Eliminare questo esercizio dalla libreria?")) {
      try { await api(`/exercises/${del.dataset.del}`, { method: "DELETE" }); toast("Esercizio eliminato"); renderExercises(); }
      catch (err) { toast(err.message, true); }
    }
  };
}

/* ---- Ritaglio foto: riquadro 4:3 identico a quello della scheda.
   Trascina per spostare, rotella/slider per lo zoom. "Intera" mostra tutta la foto. */
const CROP_W = 1200, CROP_H = 900;
function createCropper(frame, onChange) {
  const im = new Image();
  im.className = "crop-img";
  im.draggable = false;
  let s = 1, x = 0, y = 0, minS = 1, maxS = 4, coverS = 1, loaded = false;
  const W = () => frame.clientWidth, H = () => frame.clientHeight;

  const clamp = () => {
    const w = im.naturalWidth * s, h = im.naturalHeight * s;
    x = w <= W() ? (W() - w) / 2 : Math.min(0, Math.max(W() - w, x));
    y = h <= H() ? (H() - h) / 2 : Math.min(0, Math.max(H() - h, y));
  };
  const render = () => {
    clamp();
    im.style.width = im.naturalWidth * s + "px";
    im.style.transform = `translate(${x}px, ${y}px)`;
    onChange && onChange(api);
  };
  const zoomTo = (ns, cx = W() / 2, cy = H() / 2) => {
    ns = Math.min(maxS, Math.max(minS, ns));
    x = cx - (cx - x) * (ns / s);
    y = cy - (cy - y) * (ns / s);
    s = ns; render();
  };

  let drag = null;
  frame.addEventListener("pointerdown", e => {
    if (!loaded) return;
    drag = { px: e.clientX, py: e.clientY, x, y };
    frame.setPointerCapture(e.pointerId);
    frame.classList.add("dragging");
  });
  frame.addEventListener("pointermove", e => {
    if (!drag) return;
    x = drag.x + e.clientX - drag.px; y = drag.y + e.clientY - drag.py; render();
  });
  const end = () => { drag = null; frame.classList.remove("dragging"); };
  frame.addEventListener("pointerup", end);
  frame.addEventListener("pointercancel", end);
  frame.addEventListener("wheel", e => {
    if (!loaded) return;
    e.preventDefault();
    const r = frame.getBoundingClientRect();
    zoomTo(s * (e.deltaY < 0 ? 1.08 : 1 / 1.08), e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });

  const api = {
    get loaded() { return loaded; },
    get zoom() { return Math.log(s / minS) / Math.log(maxS / minS); }, // 0..1 per lo slider
    setZoom(t) { zoomTo(minS * Math.pow(maxS / minS, t)); },
    load(src) {
      return new Promise((res, rej) => {
        im.onload = () => {
          loaded = true;
          frame.querySelector(".crop-empty")?.remove();
          frame.appendChild(im);
          minS = Math.min(W() / im.naturalWidth, H() / im.naturalHeight);  // foto intera
          coverS = Math.max(W() / im.naturalWidth, H() / im.naturalHeight); // riempie il riquadro
          maxS = Math.max(coverS * 3, minS * 4);
          s = minS; render(); res();
        };
        im.onerror = () => rej(new Error("Impossibile leggere l'immagine"));
        im.src = src;
      });
    },
    fit() { s = minS; render(); },
    fill() { s = coverS; render(); },
    draw(canvas) { // disegna esattamente ciò che si vede nel riquadro
      const ctx = canvas.getContext("2d"), k = canvas.width / W();
      ctx.fillStyle = "#fff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      if (!loaded) return;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(im, x * k, y * k, im.naturalWidth * s * k, im.naturalHeight * s * k);
    },
    toBlob() {
      const c = document.createElement("canvas");
      c.width = CROP_W; c.height = CROP_H;
      api.draw(c);
      return new Promise(r => c.toBlob(r, "image/jpeg", 0.9));
    },
  };
  return api;
}

function exerciseForm(ex = {}) {
  let cropper, touched = false;
  openModal({
    title: ex.id ? "Modifica esercizio" : "Nuovo esercizio",
    wide: true,
    body: `
      <div class="ex-form">
        <div class="form-grid">
          <label class="span2">Nome<input name="name" required value="${esc(ex.name)}" placeholder="Es. Panca piana bilanciere"></label>
          <label>Gruppo muscolare<input name="muscle_group" list="dl-groups" value="${esc(ex.muscle_group)}" placeholder="Es. Petto"></label>
          <label>Attrezzo<input name="equipment" value="${esc(ex.equipment)}" placeholder="Es. Bilanciere"></label>
          <label class="span2">Link esecuzione (YouTube, Instagram…)<input name="link" value="${esc(ex.link)}" placeholder="https://…"></label>
          <div class="span2 defaults-box">
            <div class="crop-label">${icon("clock")} Valori predefiniti — compilati in automatico quando aggiungi l'esercizio a una scheda (poi modificabili scheda per scheda)</div>
            <div class="defaults-grid">
              <label>Serie<input name="default_sets" value="${esc(ex.default_sets)}" placeholder="4"></label>
              <label>Ripetizioni<input name="default_reps" value="${esc(ex.default_reps)}" placeholder="8-10"></label>
              <label>Recupero (sec)<input name="default_rest" value="${esc(ex.default_rest)}" placeholder='90&quot;'></label>
            </div>
          </div>
          <label class="span2">Descrizione / indicazioni tecniche<textarea name="description" rows="3">${esc(ex.description)}</textarea></label>
        </div>

        <div class="crop-panel">
          <div class="crop-label">Foto — trascina per spostarla, usa la rotella o lo slider per lo zoom</div>
          <div class="crop-frame" id="crop-frame">
            <div class="crop-empty"><span class="empty-ico">${icon("camera")}</span>Scegli o incolla (Ctrl+V) una foto</div>
          </div>
          <div class="crop-tools">
            <label class="btn ghost sm file-btn">${icon("camera")} Scegli foto<input type="file" id="img-file" accept="image/*" hidden></label>
            <button type="button" class="btn ghost sm" id="crop-fit" disabled title="Mostra tutta la foto">${icon("expand")} Intera</button>
            <button type="button" class="btn ghost sm" id="crop-fill" disabled title="Riempi tutto il riquadro">${icon("fill")} Riempi</button>
            <input type="range" id="crop-zoom" min="0" max="1000" value="0" disabled aria-label="Zoom">
          </div>
          ${ex.image ? `<label class="check small"><input type="checkbox" name="remove_image"> Rimuovi foto</label>` : ""}

          <div class="crop-label">Anteprima nella scheda</div>
          <div class="sheet-ex crop-preview">
            <div class="sheet-ex-img"><canvas id="crop-canvas" width="400" height="300"></canvas></div>
            <div class="sheet-ex-body">
              <div class="sheet-ex-title"><h3 id="pv-ex-name">${esc(ex.name || "Nome esercizio")}</h3>
                <span class="chip" id="pv-ex-group">${esc(ex.muscle_group || "Gruppo")}</span></div>
              <div class="sheet-params"><div><span>Serie</span><b>4</b></div><div><span>Ripetizioni</span><b>8-10</b></div></div>
            </div>
          </div>
        </div>
      </div>`,
    onOpen: dlg => {
      const canvas = $("#crop-canvas"), zoom = $("#crop-zoom");
      cropper = createCropper($("#crop-frame"), c => {
        c.draw(canvas);
        zoom.value = Math.round(c.zoom * 1000);
      });
      const enable = () => ["#crop-fit", "#crop-fill", "#crop-zoom"].forEach(s => ($(s).disabled = false));
      const loadFile = file => {
        if (!file || !file.type.startsWith("image/")) return toast("Il file non è un'immagine", true);
        const r = new FileReader();
        r.onload = () => cropper.load(r.result).then(() => { touched = true; enable(); }).catch(e => toast(e.message, true));
        r.readAsDataURL(file);
      };
      // le modifiche all'inquadratura contano come "da salvare"
      $("#crop-frame").addEventListener("pointerdown", () => cropper.loaded && (touched = true));
      $("#crop-frame").addEventListener("wheel", () => cropper.loaded && (touched = true));
      $("#crop-fit").onclick = () => { cropper.fit(); touched = true; };
      $("#crop-fill").onclick = () => { cropper.fill(); touched = true; };
      zoom.oninput = () => { cropper.setZoom(zoom.value / 1000); touched = true; };
      $("#img-file").onchange = e => loadFile(e.target.files[0]);
      dlg.onpaste = e => {
        const file = [...(e.clipboardData?.files || [])].find(f => f.type.startsWith("image/"));
        if (file) { e.preventDefault(); loadFile(file); }
      };
      $("input[name=name]", dlg).addEventListener("input", e => ($("#pv-ex-name").textContent = e.target.value || "Nome esercizio"));
      $("input[name=muscle_group]", dlg).addEventListener("input", e => ($("#pv-ex-group").textContent = e.target.value || "Gruppo"));
      const restIn = $("input[name=default_rest]", dlg);
      if (restIn) restIn.addEventListener("blur", () => (restIn.value = fmtRest(restIn.value)));
      if (ex.image) cropper.load(img(ex.image)).then(enable).catch(() => {});
      else cropper.draw(canvas);
    },
    onSubmit: async f => {
      const fd = new FormData(f);
      fd.delete("image");
      if (touched && cropper.loaded && !f.remove_image?.checked) {
        fd.set("image", await cropper.toBlob(), "foto.jpg");
      }
      fd.set("remove_image", f.remove_image?.checked ? "1" : "0");
      await api(ex.id ? `/exercises/${ex.id}` : "/exercises", { method: ex.id ? "PUT" : "POST", body: fd });
      toast("Esercizio salvato");
      renderExercises();
    },
  });
}

// ================================================================== ATLETI
async function renderAthletes() {
  const list = await api("/athletes");
  app.innerHTML = `
    ${hero({
      eyebrow: "I tuoi clienti", title: "Atleti", ic: "users",
      sub: `${list.length} ${list.length == 1 ? "atleta registrato" : "atleti registrati"}.`,
      actions: `<button class="btn light" id="new-ath">${icon("plus")} Nuovo atleta</button>`,
    })}
    ${list.length ? `<div class="card table-wrap"><table class="table">
        <thead><tr><th>Atleta</th><th>Obiettivo</th><th>Contatti</th><th>Schede</th><th></th></tr></thead>
        <tbody>${list.map(a => `<tr>
          <td><div class="person"><span class="avatar">${esc(initials(a.name))}</span><div><b>${esc(a.name)}</b>
            ${a.birth_date ? `<small class="muted meta-line">${icon("cake")} ${fmtDate(a.birth_date)}</small>` : ""}</div></div></td>
          <td>${a.goal ? `<span class="meta"><span class="meta-ico">${icon("target")}</span>${esc(a.goal)}</span>` : `<span class="muted">—</span>`}</td>
          <td class="small">
            ${a.phone ? `<a class="meta-line" href="tel:${esc(a.phone.replace(/\s+/g, ""))}">${icon("phone")} ${esc(a.phone)}</a>` : ""}
            ${a.email ? `<a class="meta-line" href="mailto:${esc(a.email)}">${icon("mail")} ${esc(a.email)}</a>` : ""}</td>
          <td><button class="btn ghost sm count-btn" data-show="${a.id}" title="Vedi le schede">${icon("file")} ${a.programs} ${icon("right")}</button></td>
          <td class="right nowrap">
            <button class="btn ghost sm" data-edit="${a.id}">${icon("edit")} Modifica</button>
            <button class="btn ghost sm sq danger" data-del="${a.id}" title="Elimina">${icon("trash")}</button>
          </td></tr>`).join("")}</tbody></table></div>`
      : emptyBox("users", "Nessun atleta. Aggiungi il primo!")}`;

  $("#new-ath").onclick = () => athleteForm();
  app.onclick = async e => {
    const ed = e.target.closest("[data-edit]"), del = e.target.closest("[data-del]"), show = e.target.closest("[data-show]");
    if (!location.hash.startsWith("#/atleti")) return;
    if (ed) athleteForm(list.find(x => x.id == ed.dataset.edit));
    if (show) { sessionStorage.setItem("filterAthlete", show.dataset.show); location.hash = "#/schede"; }
    if (del && await confirmBox("Eliminare questo atleta? Le sue schede resteranno senza atleta associato.")) {
      await api(`/athletes/${del.dataset.del}`, { method: "DELETE" }); toast("Atleta eliminato"); renderAthletes();
    }
  };
}

function athleteForm(a = {}) {
  openModal({
    title: a.id ? "Modifica atleta" : "Nuovo atleta",
    body: `
      <div class="form-grid">
        <label class="span2">Nome e cognome<input name="name" required value="${esc(a.name)}"></label>
        <label>Telefono<input name="phone" value="${esc(a.phone)}"></label>
        <label>Email<input name="email" type="email" value="${esc(a.email)}"></label>
        <label>Data di nascita<input name="birth_date" type="date" value="${esc(a.birth_date)}"></label>
        <label>Obiettivo<input name="goal" value="${esc(a.goal)}"></label>
        <label class="span2">Note (infortuni, preferenze…)<textarea name="notes" rows="3">${esc(a.notes)}</textarea></label>
      </div>`,
    onSubmit: async f => {
      const body = Object.fromEntries(new FormData(f));
      await api(a.id ? `/athletes/${a.id}` : "/athletes", { method: a.id ? "PUT" : "POST", body });
      toast("Atleta salvato"); renderAthletes();
    },
  });
}

// ================================================================== IMPOSTAZIONI
async function renderSettings() {
  await loadSettings();
  const s = { ...SETTINGS };
  app.innerHTML = `
    ${hero({
      eyebrow: "Personalizzazione", title: "La mia grafica", ic: "palette",
      sub: "Logo, colori, font e contatti: tutto il programma e le schede si adattano al tuo stile.",
      actions: `<button class="btn light" id="save-set">${icon("save")} Salva</button>`,
    })}
    <div class="settings-layout">
      <section class="card">
        <div class="section-title"><span class="info-ico">${icon("idcard")}</span><h3>Identità</h3></div>
        <div class="form-grid">
          <label>Nome / brand<input data-s="brand_name" value="${esc(s.brand_name)}"></label>
          <label>Sottotitolo<input data-s="brand_subtitle" value="${esc(s.brand_subtitle)}"></label>
          <div class="span2 img-field">
            <div class="img-preview logo-prev">${s.logo ? `<img src="${img(s.logo)}">` : `${icon("image")}<span>Nessun logo</span>`}</div>
            <div>
              <label class="btn ghost sm file-btn">${icon("image")} Carica logo<input type="file" id="logo-file" accept="image/*" hidden></label>
              ${s.logo ? `<button class="btn ghost sm danger" id="logo-del">${icon("trash")} Rimuovi</button>` : ""}
            </div>
          </div>
        </div>
        <div class="section-title"><span class="info-ico">${icon("palette")}</span><h3>Colori e font</h3></div>
        <div class="form-grid">
          <label>Colore principale<input type="color" data-s="primary_color" value="${esc(s.primary_color)}"></label>
          <label>Colore scuro<input type="color" data-s="secondary_color" value="${esc(s.secondary_color)}"></label>
          <label>Colore di sfondo riquadri<input type="color" data-s="accent_color" value="${esc(s.accent_color)}"></label>
          <label>Font<select data-s="font">${FONTS.map(f => `<option ${f === s.font ? "selected" : ""}>${f}</option>`).join("")}</select></label>
        </div>
        <div class="section-title"><span class="info-ico">${icon("phone")}</span><h3>Contatti <small class="muted">(appaiono sulla scheda)</small></h3></div>
        <div class="form-grid">
          <label>Telefono<input data-s="contact_phone" value="${esc(s.contact_phone)}"></label>
          <label>Email<input data-s="contact_email" value="${esc(s.contact_email)}"></label>
          <label>Instagram / social<input data-s="contact_social" value="${esc(s.contact_social)}" placeholder="@nome"></label>
          <label>Sito web<input data-s="website" value="${esc(s.website)}"></label>
          <label class="span2">Frase a piè di pagina<input data-s="footer_text" value="${esc(s.footer_text)}"></label>
        </div>
      </section>

      <aside>
        <div class="card preview-card">
          <div class="section-title"><span class="info-ico">${icon("eye")}</span><h3>Anteprima</h3></div>
          <div class="mini-sheet">
            <div class="mini-head">
              <span class="deco deco-1"></span>
              ${s.logo ? `<span class="mini-logo"><img src="${img(s.logo)}"></span>` : ""}
              <div><b id="pv-name">${esc(s.brand_name)}</b><small id="pv-sub">${esc(s.brand_subtitle)}</small></div>
            </div>
            <div class="mini-day"><div><small>Giorno 1</small>Push</div><span>01</span></div>
            <div class="mini-ex"><div class="mini-img">${icon("dumbbell")}</div><div><b>Panca piana</b><div class="mini-params"><span>4 × 8</span><span>90"</span></div></div></div>
            <div class="mini-ex"><div class="mini-img">${icon("dumbbell")}</div><div><b>Military press</b><div class="mini-params"><span>3 × 10</span><span>60"</span></div></div></div>
            <div class="mini-foot" id="pv-foot">${esc(s.footer_text)}</div>
          </div>
        </div>
        <div class="card">
          <div class="section-title"><span class="info-ico">${icon("database")}</span><h3>Backup &amp; condivisione</h3></div>
          <p class="small muted">Il database si trova nella cartella <code>data</code>. Scarica periodicamente una copia di sicurezza. Per aggiornare il file tra più persone: scarica il backup, invialo (email/cloud), l'altra persona lo <b>ripristina</b> qui.</p>
          <div class="form-grid" style="gap:8px">
            <a class="btn ghost sm" href="/api/backup">${icon("download")} Scarica backup database</a>
            <label class="btn ghost sm file-btn">${icon("database")} Ripristina da file .db<input type="file" id="restore-file" accept=".db,application/octet-stream" hidden></label>
          </div>
          <p class="small muted" style="margin-top:10px"><b>Più dispositivi in rete locale:</b> chiudi il programma e riavvialo con <code>./avvia.command --lan</code> (Mac) o <code>avvia.bat --lan</code> (Windows). Altri PC/telefoni collegati alla stessa rete potranno aprire l'indirizzo mostrato nella finestra nera e lavorare sullo stesso database.</p>
        </div>

        <div class="card" id="update-card">
          <div class="section-title"><span class="info-ico">${icon("download")}</span><h3>Aggiornamenti programma</h3></div>
          <div id="update-body" class="small muted">Controllo in corso…</div>
        </div>
      </aside>
    </div>`;

  $$("[data-s]").forEach(el => el.addEventListener("input", () => {
    s[el.dataset.s] = el.value;
    DIRTY = true;
    applyBranding(s);
    $("#pv-name").textContent = s.brand_name;
    $("#pv-sub").textContent = s.brand_subtitle;
    $("#pv-foot").textContent = s.footer_text;
  }));
  $("#save-set").onclick = async () => {
    SETTINGS = await api("/settings", { method: "PUT", body: s });
    DIRTY = false; applyBranding(); toast("Grafica salvata");
  };
  $("#logo-file").onchange = async e => {
    const fd = new FormData(); fd.append("file", e.target.files[0]);
    try {
      await api("/settings/logo", { method: "POST", body: fd });
      if (DIRTY) await api("/settings", { method: "PUT", body: s });
      DIRTY = false; toast("Logo caricato"); renderSettings();
    } catch (err) { toast(err.message, true); }
  };
  $("#logo-del") && ($("#logo-del").onclick = async () => {
    await api("/settings/logo", { method: "DELETE" }); toast("Logo rimosso"); renderSettings();
  });
  renderUpdateCard();
  $("#restore-file").onchange = async e => {
    const file = e.target.files[0];
    if (!file) return;
    if (!(await confirmBox(`Ripristinare il database da "${file.name}"? Il database attuale verrà salvato come backup automatico nella cartella data.`))) {
      e.target.value = ""; return;
    }
    const fd = new FormData(); fd.append("file", file);
    try {
      await api("/restore", { method: "POST", body: fd });
      toast("Database ripristinato");
      await loadSettings();
      renderSettings();
    } catch (err) { toast(err.message, true); }
  };
}

// ------------------------------------------------------------------ avvio
(async () => {
  $$("[data-nav]").forEach(a => a.insertAdjacentHTML("afterbegin", icon(a.dataset.icon)));
  $("#modal-x").innerHTML = icon("x");
  try { await loadSettings(); } catch { /* server non raggiungibile */ }
  if (!location.hash) location.hash = "#/schede";
  router();
  checkVersion(); // in background, non blocca avvio
})();
