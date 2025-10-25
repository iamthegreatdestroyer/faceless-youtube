@echo off
REM ============================================================================
REM FACELESS YOUTUBE - API STARTUP SCRIPT (Windows)
REM ============================================================================
REM
REM Starts the FastAPI backend application
REM
REM Prerequisites:
REM   - Python 3.11+
REM   - Virtual environment created (venv/)
REM   - Dependencies installed (pip install -r requirements.txt)
REM
REM Usage: run-api.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion
title Faceless YouTube - API Server

cls
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║             FACELESS YOUTUBE - API SERVER STARTUP                         ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist venv\ (
    echo ❌ Virtual environment not found at venv\
    echo.
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated
echo.

REM Check if .env exists
if not exist .env (
    echo ❌ Configuration file not found (.env)
    echo.
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo ✓ Configuration loaded (.env)
echo.

REM Start API
echo Starting API server on http://127.0.0.1:8000
echo.
echo Documentation available at:
echo   - Swagger UI:  http://127.0.0.1:8000/docs
echo   - ReDoc:       http://127.0.0.1:8000/redoc
echo.
echo Press Ctrl+C to stop the server
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗

cd /d "%~dp0"
python -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000

exit /b 0
