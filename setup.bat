@echo off
REM ============================================================================
REM FACELESS YOUTUBE - ONE-CLICK INSTALLER (WINDOWS)
REM ============================================================================
REM
REM This script provides the complete setup experience for the
REM Faceless YouTube Automation Platform on Windows systems.
REM
REM Features:
REM   - Environment detection and validation
REM   - Python and Node.js dependency checks
REM   - Virtual environment setup
REM   - Interactive configuration wizard
REM   - Database initialization
REM   - One-click startup options
REM
REM Date: October 25, 2025
REM ============================================================================

setlocal enabledelayedexpansion
title Faceless YouTube - Setup Wizard

cls
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║         🚀  FACELESS YOUTUBE - ONE-CLICK INSTALLATION WIZARD  🚀          ║
echo ║                                                                            ║
echo ║                    Automating Security & Content Creation                 ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Get project root
set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM ============================================================================
REM STEP 1: CHECK SYSTEM REQUIREMENTS
REM ============================================================================

echo [1/5] Checking system requirements...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11 or higher from:
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js 18+ from:
    echo    https://nodejs.org/
    pause
    exit /b 1
)

for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo ✓ Node.js %NODE_VERSION% found

echo ✓ All system requirements met
echo.

REM ============================================================================
REM STEP 2: CREATE VIRTUAL ENVIRONMENT
REM ============================================================================

echo [2/5] Setting up Python environment...
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated
echo.

REM ============================================================================
REM STEP 3: INSTALL DEPENDENCIES
REM ============================================================================

echo [3/5] Installing dependencies...
echo.

echo Installing Python dependencies...
pip install -r requirements-dev.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    echo Run: pip install -r requirements-dev.txt
    pause
    exit /b 1
)
echo ✓ Python dependencies installed

echo Installing Node.js dependencies...
if exist dashboard\package.json (
    cd dashboard
    call npm install >nul 2>&1
    if errorlevel 1 (
        echo ❌ Failed to install Node.js dependencies
        cd ..
        pause
        exit /b 1
    )
    echo ✓ Node.js dependencies installed
    cd ..
) else (
    echo ⚠ dashboard\package.json not found, skipping npm install
)

echo.

REM ============================================================================
REM STEP 4: CONFIGURATION WIZARD
REM ============================================================================

echo [4/5] Running configuration wizard...
echo.

REM Run the Python setup wizard
python scripts\setup_wizard.py
if errorlevel 1 (
    echo ❌ Setup wizard failed
    pause
    exit /b 1
)

echo.

REM ============================================================================
REM STEP 5: COMPLETION
REM ============================================================================

echo [5/5] Installation complete!
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                        ✓ SETUP COMPLETED SUCCESSFULLY                      ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.
echo NEXT STEPS:
echo.
echo 1. Start the API server:
echo    python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
echo.
echo 2. In another terminal, start the Dashboard:
echo    cd dashboard
echo    npm run dev
echo.
echo 3. Open your browser:
echo    http://127.0.0.1:3000
echo.
echo Documentation: Check README.md for detailed setup instructions
echo.
echo Press any key to exit...
pause >nul

exit /b 0
