@echo off
REM ============================================================================
REM FACELESS YOUTUBE - DASHBOARD STARTUP SCRIPT (Windows)
REM ============================================================================
REM
REM Starts the React frontend dashboard
REM
REM Prerequisites:
REM   - Node.js 18+
REM   - npm installed
REM   - Dependencies installed (npm install in dashboard/)
REM
REM Usage: run-dashboard.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion
title Faceless YouTube - Dashboard

cls
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║           FACELESS YOUTUBE - DASHBOARD STARTUP                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check if dashboard directory exists
if not exist dashboard\ (
    echo ❌ Dashboard directory not found at dashboard\
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist dashboard\node_modules\ (
    echo ⚠ Dependencies not installed in dashboard\
    echo.
    echo Installing dependencies with npm install...
    cd dashboard
    call npm install
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✓ Dependencies installed
    cd ..
) else (
    echo ✓ Dependencies found
)

echo ✓ Dashboard ready
echo.

REM Navigate to dashboard
cd dashboard

REM Start development server
echo Starting dashboard server on http://127.0.0.1:3000
echo.
echo Dashboard will open in your default browser automatically
echo.
echo Press Ctrl+C to stop the server
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo.

call npm start

exit /b 0
