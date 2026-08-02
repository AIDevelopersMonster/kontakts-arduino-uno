@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python Launcher py.exe not found. Install Python 3.10 or newer.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3 -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r gui\requirements.txt || exit /b 1
".venv\Scripts\python.exe" -m gui.app
if errorlevel 1 pause
