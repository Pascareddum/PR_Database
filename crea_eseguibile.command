#!/bin/bash
# Le Schede — creazione eseguibile per macOS (PyInstaller)
# Installa da solo Python 3.12 in user-space tramite 'uv' (niente password admin,
# niente Xcode). Produce dist/LeSchede, un unico file che gira anche su Mac
# senza Python installato (stessa architettura: Intel oppure Apple Silicon).
cd "$(dirname "$0")"

trap 'echo; echo "  Operazione non riuscita."; read -p "Premi INVIO per chiudere..." _' ERR
set -e

# 'uv' si installa in ~/.local/bin: aggiungilo al PATH per questa sessione.
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# ---------------------------------------------------------------- 1) uv
if ! command -v uv >/dev/null 2>&1; then
  echo "  Installo 'uv' (serve una sola volta, nessuna password richiesta)..."
  if ! command -v curl >/dev/null 2>&1; then
    echo "  Errore: 'curl' non disponibile. Riprova con una connessione Internet."
    read -p "Premi INVIO per chiudere..." _
    exit 1
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo
  echo "  'uv' non trovato dopo l'installazione. Chiudi il Terminale e riapri"
  echo "  questo file. Se il problema persiste installa Python da"
  echo "    https://www.python.org/downloads/macos/"
  echo
  read -p "Premi INVIO per chiudere..." _
  exit 1
fi
echo "  uv trovato: $(command -v uv)"

# ---------------------------------------------------------------- 2) Python 3.12
echo "  Verifico Python 3.12 (scaricato in ~/.local/share/uv se mancante)..."
uv python install 3.12

# ---------------------------------------------------------------- 3) venv
VPY=".venv/bin/python"
if [ -x "$VPY" ] && ! "$VPY" -c "import sys" >/dev/null 2>&1; then
  echo "  Ambiente .venv non valido, lo ricreo..."
  rm -rf .venv
fi
if [ ! -x "$VPY" ]; then
  echo "  Creo .venv con Python 3.12..."
  uv venv .venv --python 3.12
fi

# ---------------------------------------------------------------- 4) dipendenze + pyinstaller
echo "  Installo le dipendenze (serve Internet la prima volta)..."
uv pip install --python "$VPY" -r requirements.txt pyinstaller

# ---------------------------------------------------------------- 5) Chromium
# Playwright richiede Chromium (~130MB). Scaricato per l'architettura corrente
# del Mac (Intel oppure Apple Silicon). L'utente finale avrà download automatico
# al primo PDF se mancante (vedi pdf.py _install_chromium).
echo "  Scarico Chromium per Playwright (~130MB, solo prima volta)..."
"$VPY" -m playwright install chromium

# ---------------------------------------------------------------- 6) build
echo "  Creo l'eseguibile, attendi..."
rm -rf build
# Su macOS il separatore di --add-data è ":" (non ";" come su Windows).
# NIENTE --windowed: lascia visibile la finestra del Terminale per poter
# spegnere il programma chiudendola, come su Windows.
# NOTA architettura: --onefile produce un binario per l'architettura della
# macchina corrente. Su Apple Silicon il bundle è arm64, su Intel è x86_64.
# Per distribuire a entrambi: eseguire questo script una volta su Mac Intel
# (o via "arch -x86_64 /bin/bash crea_eseguibile.command" con Rosetta 2 +
# Python x86_64) e una volta su Apple Silicon, generando 2 binari distinti.
"$VPY" -m PyInstaller --noconfirm --clean --onefile --name LeSchede \
  --add-data "$PWD/static:static" \
  --collect-all playwright \
  --hidden-import playwright.sync_api \
  --distpath "$PWD/dist" --workpath "$PWD/build" --specpath "$PWD/build" \
  "$PWD/app.py"

echo
echo "  Fatto! L'eseguibile si trova in: dist/LeSchede"
echo "  Il database verrà creato nella cartella 'data' accanto al file."
echo
echo "  Per aprirlo: doppio clic su dist/LeSchede."
echo "  La prima volta macOS potrebbe bloccarlo (sviluppatore non identificato):"
echo "  tasto destro -> 'Apri' -> 'Apri' una sola volta."
read -p "Premi INVIO per chiudere..." _
