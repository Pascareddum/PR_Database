@echo off
setlocal
title Le Schede - Creazione eseguibile
REM Crea un unico LeSchede.exe (non serve Python sul PC di destinazione).
REM Funziona su qualsiasi PC Windows: se manca Python propone di installarlo.
cd /d "%~dp0"

REM ---------------------------------------------------------------- trova Python
call "%~dp0_trova_python.bat"
if errorlevel 1 goto :errore
echo  Python trovato: %PY%

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
  echo  Creo l'ambiente .venv...
  %PY% -m venv ".venv"
  if errorlevel 1 goto :errore
)

REM ---------------------------------------------------------------- dipendenze
echo  Installo le dipendenze ^(serve Internet la prima volta^)...
"%VPY%" -m pip install --quiet --disable-pip-version-check -r requirements.txt pyinstaller
if errorlevel 1 goto :errore

REM ---------------------------------------------------------------- build
echo  Creo l'eseguibile, attendi...
if exist "build" rmdir /s /q "build"
"%VPY%" -m PyInstaller --noconfirm --clean --onefile --name LeSchede ^
  --add-data "%~dp0static;static" ^
  --distpath "%~dp0dist" --workpath "%~dp0build" --specpath "%~dp0build" ^
  "%~dp0app.py"
if errorlevel 1 (
  echo.
  echo  Errore durante la creazione. Se LeSchede.exe e' aperto, chiudilo e riprova.
  goto :errore
)

echo.
echo  Fatto! L'eseguibile si trova in: "%~dp0dist\LeSchede.exe"
echo  Il database verra' creato nella cartella "data" accanto all'exe.
pause
exit /b 0

:errore
echo.
echo  Operazione non riuscita.
pause
exit /b 1
