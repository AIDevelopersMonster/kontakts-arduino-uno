@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
)

".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r gui\requirements.txt
if errorlevel 1 goto :error

".venv\Scripts\python.exe" -m gui.app
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo GUI Blink could not start. Check that Python 3 is installed.
pause
exit /b 1
