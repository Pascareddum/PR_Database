#!/bin/bash
# Le Schede — creazione eseguibile per macOS (PyInstaller)
# Produce dist/LeSchede (binario) e dist/LeSchede.app (bundle macOS).
# NOTA: l'app .app funziona sul Mac su cui viene compilata e su Mac con la
# stessa architettura (Intel oppure Apple Silicon). Per entrambe serve
# ricompilare su un Mac di quel tipo.
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
echo "  Python trovato: $PY"

# ---------------------------------------------------------------- venv (ricrea se non valido)
VPY=".venv/bin/python"
if [ -x "$VPY" ]; then
  if ! "$VPY" -c "import sys" >/dev/null 2>&1; then
    echo "  Ambiente .venv non valido, lo ricreo..."
    rm -rf .venv
  fi
fi
if [ ! -x "$VPY" ]; then
  echo "  Creo l'ambiente .venv..."
  "$PY" -m venv .venv
fi

# ---------------------------------------------------------------- dipendenze + pyinstaller
echo "  Installo le dipendenze (serve Internet la prima volta)..."
"$VPY" -m pip install --quiet --disable-pip-version-check -r requirements.txt pyinstaller

# ---------------------------------------------------------------- build
echo "  Creo l'eseguibile, attendi..."
rm -rf build
# Su macOS il separatore di --add-data è ":" (non ";" come su Windows).
# NIENTE --windowed: vogliamo la finestra del Terminale visibile per poter
# spegnere il programma (chiudendo la finestra), come succede su Windows.
"$VPY" -m PyInstaller --noconfirm --clean --onefile --name LeSchede \
  --add-data "static:static" \
  --distpath "dist" --workpath "build" --specpath "build" \
  app.py

echo
echo "  Fatto! L'eseguibile si trova in: dist/LeSchede"
echo "  Il database verrà creato nella cartella 'data' accanto al file."
echo
echo "  Per aprirlo: doppio clic su dist/LeSchede."
echo "  La prima volta macOS potrebbe bloccarlo (sviluppatore non identificato):"
echo "  tasto destro -> 'Apri' -> 'Apri' una sola volta."
read -p "Premi INVIO per chiudere..." _
