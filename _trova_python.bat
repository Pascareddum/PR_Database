@echo off
REM Usato da avvia.bat e crea_eseguibile.bat (non serve aprirlo direttamente).
REM Imposta la variabile PY con un comando Python 3.8+ funzionante.
REM Se Python non c'e', propone di installarlo automaticamente con winget.
set "PY="
call :cerca
if defined PY exit /b 0

echo.
echo  Python non e' installato su questo PC.
where winget >nul 2>nul
if errorlevel 1 goto :manuale

choice /c SN /m " Vuoi installarlo ora automaticamente"
if errorlevel 2 goto :manuale
echo.
echo  Installazione di Python in corso, puo' richiedere qualche minuto...
winget install -e --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
call :cerca
if defined PY (
  echo  Python installato correttamente.
  exit /b 0
)

:manuale
echo.
echo  Installa Python manualmente da https://www.python.org/downloads/
echo  spuntando "Add python.exe to PATH", poi riavvia questo file.
exit /b 1

REM ------------------------------------------------------------------------
:cerca
REM 1) comandi nel PATH
call :prova py -3
if defined PY exit /b 0
call :prova python
if defined PY exit /b 0
call :prova python3
if defined PY exit /b 0
REM 2) percorsi di installazione standard (utile subito dopo l'installazione,
REM    quando il PATH di questa finestra non e' ancora aggiornato)
if exist "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" call :prova "%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" -3
if defined PY exit /b 0
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*") do (
  if not defined PY if exist "%%~D\python.exe" call :prova "%%~D\python.exe"
)
exit /b 0

:prova
%* -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>nul
if errorlevel 1 exit /b 1
set "PY=%*"
exit /b 0
