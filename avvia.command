#!/bin/bash
# Le Schede — avvio per macOS (doppio clic su questo file)
set -e
cd "$(dirname "$0")"

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
if [ -x "$VPY" ]; then
  if ! "$VPY" -c "import sys" >/dev/null 2>&1; then
    echo "  Ambiente .venv non valido, lo ricreo..."
    rm -rf .venv
  fi
fi
if [ ! -x "$VPY" ]; then
  echo "  Prima installazione in corso, attendi qualche secondo..."
  "$PY" -m venv .venv
fi

# ---------------------------------------------------------------- dipendenze
if ! "$VPY" -c "import flask, reportlab" >/dev/null 2>&1; then
  echo "  Installo le dipendenze (serve Internet)..."
  "$VPY" -m pip install --quiet --disable-pip-version-check -r requirements.txt
fi

# ---------------------------------------------------------------- avvio
# Se vuoi condividere il programma in rete locale (altri PC/telefoni di casa/studio),
# avvia con: ./avvia.command --lan
exec "$VPY" app.py "$@"
