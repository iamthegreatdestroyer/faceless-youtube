@echo off
REM ============================================================================
REM FACELESS YOUTUBE - IMPROVED INSTALLER (WINDOWS)
REM ============================================================================

setlocal enabledelayedexpansion
title Faceless YouTube - Setup Wizard

cls
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║         🚀  FACELESS YOUTUBE - ONE-CLICK INSTALLATION WIZARD  🚀          ║
echo ║                                                                            ║
echo ║                    Automating Security ^& Content Creation                 ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Navigate to project root
echo Locating project directory...
pushd "%~dp0"
cd ..\..
set "PROJECT_ROOT=%CD%"
echo Project root: %PROJECT_ROOT%
echo.

REM ============================================================================
REM STEP 1: CHECK SYSTEM REQUIREMENTS
REM ============================================================================

echo [1/5] Checking system requirements...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo. ❌ Python not found. Please install Python 3.11 or higher from:
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo. ✓ Python %PYTHON_VERSION% found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo. ❌ Node.js not found. Please install Node.js 18+ from:
    echo    https://nodejs.org/
    pause
    exit /b 1
)

for /f %%i in ('node --version') do set NODE_VERSION=%%i
echo. ✓ Node.js %NODE_VERSION% found

echo. ✓ All system requirements met
echo.

REM ============================================================================
REM STEP 2: CREATE VIRTUAL ENVIRONMENT
REM ============================================================================

echo [2/5] Setting up Python environment...
echo.

if not exist "%PROJECT_ROOT%\venv" (
    echo Creating virtual environment...
    cd /d "%PROJECT_ROOT%"
    python -m venv venv
    if errorlevel 1 (
        echo. ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo. ✓ Virtual environment created
) else (
    echo. ✓ Virtual environment already exists
)

REM Activate virtual environment
call "%PROJECT_ROOT%\venv\Scripts\activate.bat"
if errorlevel 1 (
    echo. ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

cd /d "%PROJECT_ROOT%"
echo. ✓ Virtual environment activated
echo.

REM ============================================================================
REM STEP 3: INSTALL DEPENDENCIES
REM ============================================================================

echo [3/5] Installing dependencies...
echo.

echo Installing Python dependencies from %PROJECT_ROOT%\requirements-dev.txt...
pip install -r "%PROJECT_ROOT%\requirements-dev.txt"
if errorlevel 1 (
    echo. ❌ Failed to install Python dependencies
    echo. Run manually: pip install -r requirements-dev.txt
    pause
    exit /b 1
)
echo. ✓ Python dependencies installed
echo.

echo Installing Node.js dependencies...
if exist "%PROJECT_ROOT%\dashboard\package.json" (
    cd /d "%PROJECT_ROOT%\dashboard"
    call npm install
    if errorlevel 1 (
        echo. ❌ Failed to install Node.js dependencies
        cd /d "%PROJECT_ROOT%"
        pause
        exit /b 1
    )
    echo. ✓ Node.js dependencies installed
    cd /d "%PROJECT_ROOT%"
) else (
    echo. ⚠ dashboard\package.json not found, skipping npm install
)

echo.

REM ============================================================================
REM STEP 4: CONFIGURATION WIZARD
REM ============================================================================

echo [4/5] Running configuration wizard...
echo.

REM Check if setup_wizard.py exists
if exist "%PROJECT_ROOT%\scripts\setup_wizard.py" (
    python "%PROJECT_ROOT%\scripts\setup_wizard.py"
    if errorlevel 1 (
        echo. ⚠ Setup wizard encountered an issue (may be non-critical)
        echo. Continuing with installation...
    )
) else (
    echo. ⚠ setup_wizard.py not found at %PROJECT_ROOT%\scripts\setup_wizard.py
    echo. Skipping configuration wizard
)

echo.

REM ============================================================================
REM STEP 5: COMPLETION
REM ============================================================================

cd /d "%PROJECT_ROOT%"
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

popd
exit /b 0
