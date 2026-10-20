@echo off
setlocal
cd /d "%~dp0"
set "PF_MODE=%~1"
if "%PF_MODE%"=="" set "PF_MODE=modern"
if /I "%PF_MODE%"=="modern" goto modern
if /I "%PF_MODE%"=="legacy" goto legacy
echo Usage: run_windows.bat modern ^| legacy
exit /b 2
:modern
set "PHOENIXFORGE_QT=pyside6"
goto run
:legacy
set "PHOENIXFORGE_QT=pyside2"
:run
if not exist ".venv-%PF_MODE%\Scripts\python.exe" (
  echo Run install_windows.bat %PF_MODE% first.
  pause
  exit /b 1
)
".venv-%PF_MODE%\Scripts\python.exe" -m app
if errorlevel 1 pause
