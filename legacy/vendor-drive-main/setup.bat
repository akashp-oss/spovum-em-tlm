@echo off
REM Vendor Drive - one-shot setup for Windows.
cd /d "%~dp0"
echo === Vendor Drive setup ===

python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

if not exist data mkdir data
if not exist uploads mkdir uploads
if not exist .env copy .env.example .env >nul

echo.
echo Done. Two things left:
echo   1. Open .env and set SITE_PASSWORD (and paste your free Gemini + Tavily keys).
echo   2. Run:  venv\Scripts\activate.bat ^&^& python app.py
echo      Then open http://localhost:8000
echo.
pause
