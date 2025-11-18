@echo off
setlocal enabledelayedexpansion

:: Faceless YouTube - Python Application Wrapper
:: This batch file launches the Faceless YouTube application

:: Get the directory where this batch file is located
set APP_DIR=%~dp0

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org
    echo.
    pause
    exit /b 1
)

:: Check if the main app file exists
if not exist "%APP_DIR%faceless_video_app.py" (
    echo.
    echo ERROR: faceless_video_app.py not found in %APP_DIR%
    echo.
    pause
    exit /b 1
)

:: Launch the application
echo Launching Faceless YouTube...
cd /d "%APP_DIR%"
python faceless_video_app.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    echo.
    pause
)

endlocal
