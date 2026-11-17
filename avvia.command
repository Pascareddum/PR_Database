#!/bin/bash
# Le Schede — avvio per macOS (doppio clic su questo file)
cd "$(dirname "$0")"

# Tiene aperta la finestra del Terminale in caso di errore (per leggere il messaggio).
trap 'echo; echo "  Avvio non riuscito."; read -p "Premi INVIO per chiudere..." _' ERR
set -e

# ---------------------------------------------------------------- trova Python 3
PY=""
for c in python3.12 python3.11 python3.10 python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done

if [ -z "$PY" ]; then
  echo
  echo "  Python 3 non trovato."
  echo "  Installa Python 3 da https://www.python.org/downloads/macos/"
  echo "  (oppure con Homebrew: brew install python)"
  echo
  read -p "Premi INVIO per chiudere..." _
  exit 1
fi

# ---------------------------------------------------------------- venv (ricrea se non valido)
VPY=".venv/bin/python"
make_venv() {
  # --copies: evita bug "No such file or directory" del Python di Xcode su macOS.
  "$PY" -m venv --copies .venv 2>/dev/null || "$PY" -m venv .venv
}

if [ -x "$VPY" ]; then
  if ! "$VPY" -c "import sys" >/dev/null 2>&1; then
    echo "  Ambiente .venv non valido, lo ricreo..."
    rm -rf .venv
  fi
fi
if [ ! -x "$VPY" ]; then
  echo "  Prima installazione in corso, attendi qualche secondo..."
  if ! make_venv; then
    echo
    echo "  Non riesco a creare l'ambiente virtuale con il Python di sistema."
    echo "  Soluzione: installa Python 3 'ufficiale' da"
    echo "    https://www.python.org/downloads/macos/"
    echo "  (il Python degli Xcode Command Line Tools a volte dà questo errore)."
    echo
    read -p "Premi INVIO per chiudere..." _
    exit 1
  fi
fi

# ---------------------------------------------------------------- dipendenze
if ! "$VPY" -c "import flask, reportlab" >/dev/null 2>&1; then
  echo "  Installo le dipendenze (serve Internet)..."
  "$VPY" -m pip install --quiet --disable-pip-version-check -r requirements.txt
fi

# ---------------------------------------------------------------- avvio
# Per condividere il programma in rete locale (altri PC/telefoni di casa/studio),
# avvia da Terminale: ./avvia.command --lan
exec "$VPY" app.py "$@"
