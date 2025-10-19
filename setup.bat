@echo off
echo 🚀 Faceless YouTube Setup Wizard
echo ================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

REM Create virtual environment if not exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo 📥 Installing setup wizard dependencies...
pip install -r requirements-dev.txt

python scripts\setup_wizard.py
