@echo off
REM ============================================================================
REM FACELESS YOUTUBE - DATABASE SETUP WIZARD (Windows Batch)
REM ============================================================================
REM
REM This script runs the Python database setup wizard which will:
REM   - Prompt for PostgreSQL credentials
REM   - Create the database and user
REM   - Update .env with connection string
REM   - Run database migrations
REM
REM ============================================================================

setlocal enabledelayedexpansion
title Faceless YouTube - Database Setup

echo.
echo ================================================================================
echo.
echo   ^|^| FACELESS YOUTUBE - DATABASE SETUP WIZARD ^|^|
echo.
echo   This will guide you through setting up PostgreSQL for local development
echo.
echo ================================================================================
echo.

REM Get project root
cd /d "%~dp0..\.."

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Error: Python virtual environment not found
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Activate venv and run setup script
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Running database setup wizard...
python "%~dp0setup_database.py"

if errorlevel 1 (
    echo.
    echo Setup failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo.
echo   ✓ DATABASE SETUP COMPLETE!
echo.
echo   Your .env file has been updated with the database connection details.
echo.
echo   Next, you can start the services:
echo   1. API Server: uvicorn src.api.main:app --reload
echo   2. Dashboard: npm run dev (in dashboard folder)
echo.
echo ================================================================================
echo.

pause
