@echo off
setlocal
cd /d "%~dp0"
set "PF_MODE=%~1"
if "%PF_MODE%"=="" set "PF_MODE=modern"
if /I "%PF_MODE%"=="modern" goto modern
if /I "%PF_MODE%"=="legacy" goto legacy
echo Usage: install_windows.bat modern ^| legacy
exit /b 2
:modern
set "PF_PY=-3.11-64"
set "PF_VERSION=3,11"
goto install
:legacy
set "PF_PY=-3.8-64"
set "PF_VERSION=3,8"
echo Legacy candidate: Windows 7 compatibility has NOT been verified.
:install
py %PF_PY% -c "import sys,struct; assert sys.version_info[:2]==(%PF_VERSION%) and struct.calcsize('P')==8" || goto fail
if not exist ".venv-%PF_MODE%\Scripts\python.exe" py %PF_PY% -m venv ".venv-%PF_MODE%"
if errorlevel 1 goto fail
".venv-%PF_MODE%\Scripts\python.exe" -m pip install "pip==24.0"
if errorlevel 1 goto fail
".venv-%PF_MODE%\Scripts\python.exe" -m pip install -r "requirements\%PF_MODE%.txt"
if errorlevel 1 goto fail
echo Installation completed. Run run_windows.bat %PF_MODE%
exit /b 0
:fail
echo Installation failed. Install the specified x64 Python including its py launcher.
echo Read docs\COMPATIBILITY.md for requirements and troubleshooting.
pause
exit /b 1
