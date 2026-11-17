@echo off
setlocal
title Le Schede
cd /d "%~dp0"

REM ---------------------------------------------------------------- trova Python
call "%~dp0_trova_python.bat"
if errorlevel 1 goto :errore

REM ------------------------------------------- ambiente virtuale (ricreato se non valido)
REM Una .venv copiata da un altro PC non funziona: la verifico e, se serve, la ricreo.
set "VPY=%~dp0.venv\Scripts\python.exe"
if exist "%VPY%" (
  "%VPY%" -c "import sys" >nul 2>nul
  if errorlevel 1 (
    echo  Ambiente .venv non valido su questo PC, lo ricreo...
    rmdir /s /q ".venv"
  )
)
if not exist "%VPY%" (
  echo  Prima installazione in corso, attendi qualche secondo...
  %PY% -m venv ".venv"
  if errorlevel 1 goto :errore
)

REM ------------------------------------------- dipendenze (solo se mancano: poi va anche offline)
"%VPY%" -c "import flask, reportlab" >nul 2>nul
if errorlevel 1 (
  echo  Installo le dipendenze ^(serve Internet^)...
  "%VPY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt
  if errorlevel 1 goto :errore
)

REM ---------------------------------------------------------------- avvio
REM Supporta argomenti extra: es. "avvia.bat --lan" per servire in rete locale.
"%VPY%" "%~dp0app.py" %*
pause
exit /b 0

:errore
echo.
echo  Avvio non riuscito.
pause
exit /b 1
