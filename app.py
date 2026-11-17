"""Le Schede - gestionale locale di schede di allenamento per personal trainer.

Avvio: python app.py  (oppure doppio clic su avvia.bat)
Tutti i dati restano in locale nella cartella ./data (database SQLite + immagini).
"""
import io
import os
import re
import sqlite3
import sys
import threading
import uuid
import webbrowser
from datetime import datetime

from flask import Flask, g, jsonify, request, send_from_directory, send_file, abort

if getattr(sys, "frozen", False):  # eseguibile PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
    STATIC_DIR = os.path.join(sys._MEIPASS, "static")
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
DB_PATH = os.path.join(DATA_DIR, "schede.db")
ALLOWED_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
PORT = int(os.environ.get("SCHEDE_PORT", "5057"))

# ----- versione + auto-update da GitHub Releases
VERSION = "1.0.1"
GITHUB_USER = "Pascareddum"
GITHUB_REPO = "PR_Database"

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS exercises (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    muscle_group TEXT,
    equipment    TEXT,
    description  TEXT,
    image        TEXT,
    link         TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS athletes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT,
    phone      TEXT,
    birth_date TEXT,
    goal       TEXT,
    notes      TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS programs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    athlete_id INTEGER REFERENCES athletes(id) ON DELETE SET NULL,
    title      TEXT NOT NULL,
    goal       TEXT,
    start_date TEXT,
    end_date   TEXT,
    notes      TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS program_days (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    notes      TEXT,
    position   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS day_exercises (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day_id      INTEGER NOT NULL REFERENCES program_days(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE RESTRICT,
    sets        TEXT,
    reps        TEXT,
    rest        TEXT,
    load        TEXT,
    tempo       TEXT,
    notes       TEXT,
    position    INTEGER NOT NULL DEFAULT 0
);
"""

DEFAULT_SETTINGS = {
    "brand_name": "Il Tuo Nome",
    "brand_subtitle": "Personal Trainer",
    "primary_color": "#8c1c3a",
    "secondary_color": "#3a0d1a",
    "accent_color": "#f6e9ed",
    "font": "Montserrat",
    "logo": "",
    "contact_email": "",
    "contact_phone": "",
    "contact_social": "",
    "website": "",
    "footer_text": "Allenati con costanza. I risultati arrivano.",
}


# --------------------------------------------------------------------------- DB
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    for k, v in DEFAULT_SETTINGS.items():
        db.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (k, v))
    # colonne aggiunte in versioni successive
    cols = {r[1] for r in db.execute("PRAGMA table_info(exercises)")}
    for c in ("default_sets", "default_reps", "default_rest"):
        if c not in cols:
            db.execute(f"ALTER TABLE exercises ADD COLUMN {c} TEXT")
    # vecchi colori predefiniti (arancio/blu) -> nuova palette bordeaux, solo se mai personalizzati
    for k, old in (("primary_color", "#e4572e"), ("secondary_color", "#1d2433"), ("accent_color", "#f3f4f6")):
        db.execute("UPDATE settings SET value=? WHERE key=? AND value=?", (DEFAULT_SETTINGS[k], k, old))
    db.commit()
    db.close()


def rows(cur):
    return [dict(r) for r in cur.fetchall()]


def clean(data, fields):
    out = {}
    for f in fields:
        v = data.get(f)
        if isinstance(v, str):
            v = v.strip()
        out[f] = v if v not in ("",) else None
    return out


def fmt_rest(v):
    """Recupero sempre in secondi: se stringa non vuota senza suffisso, aggiunge `"`."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    # già marcato (secondi " o minuti ')
    if s.endswith('"') or s.endswith("''") or s.endswith("'"):
        return s
    # se finisce con numero o cifra+spazi, aggiungi "
    if re.search(r"\d\s*$", s):
        return re.sub(r"\s*$", '"', s)
    return s


def error(msg, code=400):
    return jsonify({"error": msg}), code


def save_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("Formato immagine non supportato")
    name = f"{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(UPLOAD_DIR, name))
    return name


def remove_upload(name):
    if not name:
        return
    path = os.path.join(UPLOAD_DIR, os.path.basename(name))
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


# ----------------------------------------------------------------- pagine/statici
@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/uploads/<path:name>")
def uploads(name):
    return send_from_directory(UPLOAD_DIR, name)


# ------------------------------------------------------------------- settings
@app.get("/api/settings")
def get_settings():
    return jsonify({r["key"]: r["value"] for r in get_db().execute("SELECT * FROM settings")})


@app.put("/api/settings")
def put_settings():
    data = request.get_json(force=True) or {}
    db = get_db()
    for k in DEFAULT_SETTINGS:
        if k in data and k != "logo":
            db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", (k, data[k] or ""))
    db.commit()
    return get_settings()


@app.post("/api/settings/logo")
def upload_logo():
    db = get_db()
    try:
        name = save_upload(request.files.get("file"))
    except ValueError as e:
        return error(str(e))
    if not name:
        return error("Nessun file")
    old = db.execute("SELECT value FROM settings WHERE key='logo'").fetchone()
    if old:
        remove_upload(old["value"])
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES ('logo', ?)", (name,))
    db.commit()
    return get_settings()


@app.delete("/api/settings/logo")
def delete_logo():
    db = get_db()
    old = db.execute("SELECT value FROM settings WHERE key='logo'").fetchone()
    if old:
        remove_upload(old["value"])
    db.execute("UPDATE settings SET value='' WHERE key='logo'")
    db.commit()
    return get_settings()


# ------------------------------------------------------------------ esercizi
EX_FIELDS = ["name", "muscle_group", "equipment", "description", "link",
             "default_sets", "default_reps", "default_rest"]


@app.get("/api/exercises")
def list_exercises():
    q = request.args.get("q", "").strip()
    db = get_db()
    sql = """SELECT e.*, (SELECT COUNT(DISTINCT d.program_id) FROM day_exercises de
                          JOIN program_days d ON d.id = de.day_id WHERE de.exercise_id = e.id) AS usage
             FROM exercises e"""
    params = []
    if q:
        sql += " WHERE e.name LIKE ? OR e.muscle_group LIKE ? OR e.equipment LIKE ?"
        params = [f"%{q}%"] * 3
    sql += " ORDER BY e.muscle_group COLLATE NOCASE, e.name COLLATE NOCASE"
    return jsonify(rows(db.execute(sql, params)))


def _exercise_payload():
    """Accetta sia JSON sia multipart (con eventuale immagine)."""
    if request.content_type and request.content_type.startswith("multipart/"):
        return request.form.to_dict(), request.files.get("image")
    return (request.get_json(force=True) or {}), None


@app.post("/api/exercises")
def create_exercise():
    data, img = _exercise_payload()
    d = clean(data, EX_FIELDS)
    if not d["name"]:
        return error("Il nome è obbligatorio")
    d["default_rest"] = fmt_rest(d["default_rest"])
    try:
        image = save_upload(img)
    except ValueError as e:
        return error(str(e))
    db = get_db()
    cur = db.execute(
        f"INSERT INTO exercises({', '.join(EX_FIELDS)}, image) VALUES ({', '.join('?' * (len(EX_FIELDS) + 1))})",
        (*[d[f] for f in EX_FIELDS], image),
    )
    db.commit()
    return jsonify(dict(db.execute("SELECT * FROM exercises WHERE id=?", (cur.lastrowid,)).fetchone())), 201


@app.put("/api/exercises/<int:eid>")
def update_exercise(eid):
    data, img = _exercise_payload()
    d = clean(data, EX_FIELDS)
    if not d["name"]:
        return error("Il nome è obbligatorio")
    d["default_rest"] = fmt_rest(d["default_rest"])
    db = get_db()
    ex = db.execute("SELECT * FROM exercises WHERE id=?", (eid,)).fetchone()
    if not ex:
        return error("Esercizio non trovato", 404)
    image = ex["image"]
    try:
        new_img = save_upload(img)
    except ValueError as e:
        return error(str(e))
    if new_img:
        remove_upload(image)
        image = new_img
    elif data.get("remove_image") in ("1", "true", True):
        remove_upload(image)
        image = None
    db.execute(
        f"UPDATE exercises SET {', '.join(f + '=?' for f in EX_FIELDS)}, image=? WHERE id=?",
        (*[d[f] for f in EX_FIELDS], image, eid),
    )
    db.commit()
    return jsonify(dict(db.execute("SELECT * FROM exercises WHERE id=?", (eid,)).fetchone()))


@app.delete("/api/exercises/<int:eid>")
def delete_exercise(eid):
    db = get_db()
    ex = db.execute("SELECT * FROM exercises WHERE id=?", (eid,)).fetchone()
    if not ex:
        return error("Esercizio non trovato", 404)
    used = db.execute(
        """SELECT COUNT(DISTINCT d.program_id) FROM day_exercises de
           JOIN program_days d ON d.id = de.day_id WHERE de.exercise_id=?""", (eid,)).fetchone()[0]
    if used:
        return error(f"L'esercizio è usato in {used} schede: rimuovilo prima dalle schede.", 409)
    db.execute("DELETE FROM exercises WHERE id=?", (eid,))
    db.commit()
    remove_upload(ex["image"])
    return jsonify({"ok": True})


# ------------------------------------------------------------------- atleti
ATH_FIELDS = ["name", "email", "phone", "birth_date", "goal", "notes"]


@app.get("/api/athletes")
def list_athletes():
    return jsonify(rows(get_db().execute(
        """SELECT a.*, (SELECT COUNT(*) FROM programs p WHERE p.athlete_id = a.id) AS programs
           FROM athletes a ORDER BY a.name COLLATE NOCASE""")))


@app.post("/api/athletes")
def create_athlete():
    d = clean(request.get_json(force=True) or {}, ATH_FIELDS)
    if not d["name"]:
        return error("Il nome è obbligatorio")
    db = get_db()
    cur = db.execute(
        "INSERT INTO athletes(name, email, phone, birth_date, goal, notes) VALUES (?,?,?,?,?,?)",
        tuple(d[f] for f in ATH_FIELDS),
    )
    db.commit()
    return jsonify(dict(db.execute("SELECT * FROM athletes WHERE id=?", (cur.lastrowid,)).fetchone())), 201


@app.put("/api/athletes/<int:aid>")
def update_athlete(aid):
    d = clean(request.get_json(force=True) or {}, ATH_FIELDS)
    if not d["name"]:
        return error("Il nome è obbligatorio")
    db = get_db()
    db.execute(
        "UPDATE athletes SET name=?, email=?, phone=?, birth_date=?, goal=?, notes=? WHERE id=?",
        (*[d[f] for f in ATH_FIELDS], aid),
    )
    db.commit()
    return jsonify(dict(db.execute("SELECT * FROM athletes WHERE id=?", (aid,)).fetchone()))


@app.delete("/api/athletes/<int:aid>")
def delete_athlete(aid):
    db = get_db()
    db.execute("DELETE FROM athletes WHERE id=?", (aid,))
    db.commit()
    return jsonify({"ok": True})


# ------------------------------------------------------------------- schede
PRG_FIELDS = ["title", "goal", "start_date", "end_date", "notes"]


def load_program(pid):
    db = get_db()
    p = db.execute(
        """SELECT p.*, a.name AS athlete_name, a.goal AS athlete_goal, a.birth_date AS athlete_birth_date
           FROM programs p LEFT JOIN athletes a ON a.id = p.athlete_id WHERE p.id=?""",
        (pid,),
    ).fetchone()
    if not p:
        return None
    prog = dict(p)
    days = rows(db.execute("SELECT * FROM program_days WHERE program_id=? ORDER BY position, id", (pid,)))
    for day in days:
        day["exercises"] = rows(db.execute(
            """SELECT de.*, e.name, e.muscle_group, e.equipment, e.description, e.image, e.link
               FROM day_exercises de JOIN exercises e ON e.id = de.exercise_id
               WHERE de.day_id=? ORDER BY de.position, de.id""",
            (day["id"],),
        ))
    prog["days"] = days
    return prog


def save_days(db, pid, days):
    db.execute("DELETE FROM program_days WHERE program_id=?", (pid,))
    for di, day in enumerate(days or []):
        cur = db.execute(
            "INSERT INTO program_days(program_id, name, notes, position) VALUES (?,?,?,?)",
            (pid, (day.get("name") or f"Giorno {di + 1}").strip(), day.get("notes") or None, di),
        )
        day_id = cur.lastrowid
        for ei, ex in enumerate(day.get("exercises") or []):
            if not ex.get("exercise_id"):
                continue
            db.execute(
                """INSERT INTO day_exercises(day_id, exercise_id, sets, reps, rest, load, tempo, notes, position)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (day_id, int(ex["exercise_id"]), ex.get("sets"), ex.get("reps"), fmt_rest(ex.get("rest")),
                 ex.get("load"), ex.get("tempo"), ex.get("notes"), ei),
            )


@app.get("/api/programs")
def list_programs():
    return jsonify(rows(get_db().execute(
        """SELECT p.*, a.name AS athlete_name,
                  (SELECT COUNT(*) FROM program_days d WHERE d.program_id = p.id) AS days_count
           FROM programs p LEFT JOIN athletes a ON a.id = p.athlete_id
           ORDER BY p.updated_at DESC""")))


@app.get("/api/programs/<int:pid>")
def get_program(pid):
    p = load_program(pid)
    return jsonify(p) if p else error("Scheda non trovata", 404)


@app.post("/api/programs")
def create_program():
    data = request.get_json(force=True) or {}
    d = clean(data, PRG_FIELDS)
    if not d["title"]:
        return error("Il titolo è obbligatorio")
    db = get_db()
    cur = db.execute(
        "INSERT INTO programs(athlete_id, title, goal, start_date, end_date, notes) VALUES (?,?,?,?,?,?)",
        (data.get("athlete_id") or None, *[d[f] for f in PRG_FIELDS]),
    )
    save_days(db, cur.lastrowid, data.get("days"))
    db.commit()
    return jsonify(load_program(cur.lastrowid)), 201


@app.put("/api/programs/<int:pid>")
def update_program(pid):
    data = request.get_json(force=True) or {}
    d = clean(data, PRG_FIELDS)
    if not d["title"]:
        return error("Il titolo è obbligatorio")
    db = get_db()
    if not db.execute("SELECT 1 FROM programs WHERE id=?", (pid,)).fetchone():
        return error("Scheda non trovata", 404)
    db.execute(
        """UPDATE programs SET athlete_id=?, title=?, goal=?, start_date=?, end_date=?, notes=?,
           updated_at=CURRENT_TIMESTAMP WHERE id=?""",
        (data.get("athlete_id") or None, *[d[f] for f in PRG_FIELDS], pid),
    )
    save_days(db, pid, data.get("days"))
    db.commit()
    return jsonify(load_program(pid))


@app.post("/api/programs/<int:pid>/duplicate")
def duplicate_program(pid):
    p = load_program(pid)
    if not p:
        return error("Scheda non trovata", 404)
    db = get_db()
    cur = db.execute(
        "INSERT INTO programs(athlete_id, title, goal, start_date, end_date, notes) VALUES (?,?,?,?,?,?)",
        (p["athlete_id"], p["title"] + " (copia)", p["goal"], p["start_date"], p["end_date"], p["notes"]),
    )
    save_days(db, cur.lastrowid, p["days"])
    db.commit()
    return jsonify(load_program(cur.lastrowid)), 201


@app.delete("/api/programs/<int:pid>")
def delete_program(pid):
    db = get_db()
    db.execute("DELETE FROM programs WHERE id=?", (pid,))
    db.commit()
    return jsonify({"ok": True})


@app.get("/api/programs/<int:pid>/pdf")
def program_pdf(pid):
    from pdf import build_pdf
    p = load_program(pid)
    if not p:
        return error("Scheda non trovata", 404)
    settings = {r["key"]: r["value"] for r in get_db().execute("SELECT * FROM settings")}
    data = build_pdf(p, settings, UPLOAD_DIR, break_days=True)
    name = " - ".join(x for x in ("Scheda", p["title"], p.get("athlete_name")) if x)
    name = re.sub(r'[\\/:*?"<>|]+', "", name).strip() + ".pdf"
    return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=True, download_name=name)


# -------------------------------------------------------------------- backup
@app.get("/api/backup")
def backup():
    """Scarica una copia consistente del database."""
    tmp = os.path.join(DATA_DIR, "_backup_tmp.db")
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(tmp)
    src.backup(dst)
    dst.close()
    src.close()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return send_file(tmp, as_attachment=True, download_name=f"schede_backup_{stamp}.db")


@app.post("/api/restore")
def restore():
    """Sostituisce il database con un file .db caricato (condivisione tra più persone).
    Una copia del database attuale viene salvata come schede_pre_restore_<timestamp>.db."""
    f = request.files.get("file")
    if not f or not f.filename:
        return error("Nessun file")
    tmp_up = os.path.join(DATA_DIR, "_restore_tmp.db")
    f.save(tmp_up)
    # verifica che sia un DB valido
    try:
        chk = sqlite3.connect(tmp_up)
        chk.execute("SELECT 1 FROM programs LIMIT 1")
        chk.close()
    except sqlite3.Error as e:
        try:
            os.remove(tmp_up)
        except OSError:
            pass
        return error(f"File non valido: {e}")
    # chiudi connessione corrente della request (g.db) e sostituisci
    db = g.pop("db", None)
    if db is not None:
        db.close()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.isfile(DB_PATH):
        os.replace(DB_PATH, os.path.join(DATA_DIR, f"schede_pre_restore_{stamp}.db"))
    os.replace(tmp_up, DB_PATH)
    init_db()
    return jsonify({"ok": True})


# ------------------------------------------------------------- aggiornamenti
def _ver_tuple(s):
    """'1.2.3' o 'v1.2.3' -> (1,2,3); non-numerici tagliati. Serve per confronto >."""
    s = (s or "").strip().lstrip("vV")
    out = []
    for p in re.split(r"[.\-_+]", s):
        if p.isdigit():
            out.append(int(p))
        else:
            break
    return tuple(out) if out else (0,)


def _fetch_latest_release():
    import json as _json
    import urllib.request
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url, headers={
        "User-Agent": "LeSchede-updater",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=8) as r:
        return _json.loads(r.read())


def _pending_restart_version():
    try:
        with open(os.path.join(DATA_DIR, ".pending_restart"), encoding="utf-8") as f:
            v = f.read().strip()
            return v or None
    except OSError:
        return None


@app.get("/api/version")
def api_version():
    pending = _pending_restart_version()
    try:
        data = _fetch_latest_release()
    except Exception as e:
        return jsonify({"current": VERSION, "error": str(e), "pending_restart": pending})
    tag = data.get("tag_name") or ""
    latest = tag.lstrip("vV")
    zip_url = data.get("zipball_url") or \
        f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/tags/{tag}.zip"
    return jsonify({
        "current": VERSION,
        "latest": latest,
        "tag": tag,
        "update_available": _ver_tuple(latest) > _ver_tuple(VERSION),
        "pending_restart": pending,
        "notes": data.get("body") or "",
        "name": data.get("name") or tag,
        "published_at": data.get("published_at"),
        "zip_url": zip_url,
        "html_url": data.get("html_url") or f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases",
    })


def _merge_tree(src, dst):
    """Copia ricorsiva src -> dst sovrascrivendo i file (NON cancella file extra in dst)."""
    os.makedirs(dst, exist_ok=True)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            _merge_tree(s, d)
        else:
            try:
                import shutil as _sh
                _sh.copy2(s, d)
            except PermissionError:
                # file in uso (tipico su Windows con .exe): salta
                pass


PENDING_RESTART_FILE = os.path.join(DATA_DIR, ".pending_restart")


def _apply_update(info, force=False):
    """Scarica ZIP della release, sovrascrive file saltando data/.venv/.git/build/dist.
    Ritorna (ok, result). result = {"installed": <tag>, "no_update": bool} oppure messaggio errore."""
    import shutil
    import tempfile
    import urllib.request
    import zipfile

    tag = info.get("tag_name") or ""
    latest = tag.lstrip("vV")
    if _ver_tuple(latest) <= _ver_tuple(VERSION) and not force:
        return True, {"no_update": True, "current": VERSION}
    zip_url = info.get("zipball_url") or \
        f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/tags/{tag}.zip"

    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp_zip.close()
    try:
        req = urllib.request.Request(zip_url, headers={"User-Agent": "LeSchede-updater"})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp_zip.name, "wb") as out:
            shutil.copyfileobj(r, out)
    except Exception as e:
        try: os.remove(tmp_zip.name)
        except OSError: pass
        return False, f"Download fallito: {e}"

    SKIP = {"data", ".venv", "venv", "__pycache__", ".git", ".github", "build", "dist"}
    try:
        with tempfile.TemporaryDirectory() as td:
            with zipfile.ZipFile(tmp_zip.name) as z:
                z.extractall(td)
            roots = [p for p in os.listdir(td) if os.path.isdir(os.path.join(td, p))]
            if not roots:
                return False, "Pacchetto non valido"
            src_root = os.path.join(td, roots[0])
            for name in os.listdir(src_root):
                if name in SKIP:
                    continue
                s = os.path.join(src_root, name)
                d = os.path.join(BASE_DIR, name)
                if os.path.isdir(s):
                    _merge_tree(s, d)
                else:
                    try:
                        shutil.copy2(s, d)
                    except PermissionError:
                        pass
    except Exception as e:
        return False, f"Installazione fallita: {e}"
    finally:
        try: os.remove(tmp_zip.name)
        except OSError: pass

    try:
        with open(PENDING_RESTART_FILE, "w", encoding="utf-8") as f:
            f.write(latest)
    except OSError:
        pass
    return True, {"installed": latest, "previous": VERSION}


def _auto_update_boot():
    """Check + install silenzioso all'avvio. Non blocca lo startup."""
    if getattr(sys, "frozen", False):
        return
    try:
        info = _fetch_latest_release()
    except Exception:
        return
    ok, res = _apply_update(info)
    if ok and isinstance(res, dict) and res.get("installed"):
        print(f"\n  [auto-update] Nuova versione {res['installed']} installata. Riavvia per applicarla.\n", flush=True)


@app.post("/api/update")
def api_update():
    """Scarica lo ZIP della release più recente da GitHub e sovrascrive i file
    del programma. NON tocca `data/`, `.venv/`, `.git/`."""
    payload = request.get_json(force=True) or {}
    try:
        info = _fetch_latest_release()
    except Exception as e:
        return error(f"Impossibile contattare GitHub: {e}")
    ok, res = _apply_update(info, force=bool(payload.get("force")))
    if not ok:
        return error(res)
    if res.get("no_update"):
        return jsonify({"ok": True, "no_update": True, "current": VERSION})
    return jsonify({
        "ok": True,
        "installed": res["installed"],
        "previous": res["previous"],
        "message": "Aggiornamento installato. Chiudi e riapri il programma per usare la nuova versione.",
    })


@app.errorhandler(413)
def too_large(_e):
    return error("File troppo grande (max 200 MB)", 413)


init_db()

# Se è stato installato prima un aggiornamento e ora giriamo con quella versione,
# pulisci il marker 'riavvia per completare'.
try:
    _pending = _pending_restart_version()
    if _pending and _ver_tuple(_pending) <= _ver_tuple(VERSION):
        os.remove(PENDING_RESTART_FILE)
except OSError:
    pass

# Controllo+installazione silenziosa in background (solo in modalità sorgente).
threading.Thread(target=_auto_update_boot, daemon=True).start()


def _lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    lan = "--lan" in sys.argv or os.environ.get("SCHEDE_LAN") == "1"
    host = "0.0.0.0" if lan else "127.0.0.1"
    local_url = f"http://127.0.0.1:{PORT}"
    if "--no-browser" not in sys.argv:
        threading.Timer(1.2, lambda: webbrowser.open(local_url)).start()
    msg = f"\n  Le Schede è attivo su {local_url}"
    if lan:
        msg += f"\n  In rete locale: http://{_lan_ip()}:{PORT}  (apri questo indirizzo dagli altri dispositivi)"
    msg += "\n  Chiudi questa finestra per spegnere il programma.\n"
    print(msg)
    app.run(host=host, port=PORT, debug=False)
