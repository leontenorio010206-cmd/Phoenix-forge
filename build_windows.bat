@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="legacy" goto legacy
if not exist ".venv-modern\Scripts\python.exe" (
  echo Developer build: run install_windows.bat modern first.
  exit /b 1
)
".venv-modern\Scripts\python.exe" -m pip install -r requirements\build-modern.txt -r requirements\test-modern.txt
if errorlevel 1 exit /b 1
".venv-modern\Scripts\python.exe" tools\prepare_qt_sources.py
if errorlevel 1 exit /b 1
".venv-modern\Scripts\python.exe" tools\build_windows.py
exit /b %errorlevel%
:legacy
set "PHOENIXFORGE_QT=pyside2"
echo EXPERIMENTAL legacy source build. Not a verified Windows 7 release.
if not exist ".venv-legacy\Scripts\python.exe" exit /b 1
".venv-legacy\Scripts\python.exe" -m pip install -r requirements\build-legacy.txt -r requirements\test-legacy.txt
if errorlevel 1 exit /b 1
".venv-legacy\Scripts\python.exe" -m pytest -q -m "not packaged"
if errorlevel 1 exit /b 1
".venv-legacy\Scripts\python.exe" -m PyInstaller --clean --noconfirm --distpath dist\legacy --workpath build\work-legacy build\PhoenixForge_legacy.spec
exit /b %errorlevel%
