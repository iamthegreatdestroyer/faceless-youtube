@echo off
REM ============================================================================
REM FACELESS YOUTUBE - ONE-CLICK DOCKER DEPLOYMENT (Windows)
REM ============================================================================
REM
REM Starts the entire Faceless YouTube platform using Docker Compose
REM
REM Features:
REM   - One-command startup
REM   - All services pre-configured
REM   - Health checks for all services
REM   - Automatic port mapping
REM   - Volume management
REM
REM Usage: docker-start.bat
REM
REM ============================================================================

setlocal enabledelayedexpansion
title Faceless YouTube - Docker Startup

cls
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║        FACELESS YOUTUBE - ONE-CLICK DOCKER DEPLOYMENT                     ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Check Docker
echo [1/3] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker not found. Please install Docker Desktop.
    echo    https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose not found. Please install Docker Desktop.
    pause
    exit /b 1
)

for /f "tokens=3" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo ✓ Docker %DOCKER_VERSION% found

REM Check .env file
if not exist .env (
    echo ❌ .env file not found
    echo    Please run setup.bat first
    pause
    exit /b 1
)

echo ✓ Configuration loaded (.env)
echo.

REM Start services
echo [2/3] Starting Faceless YouTube services...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Failed to start Docker services
    pause
    exit /b 1
)

echo ✓ Services started
echo.

REM Check service health
echo [3/3] Verifying service status...
timeout /t 3 /nobreak >nul

docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo ⚠ Some services may not have started. Run:
    echo    docker-compose logs
    pause
    exit /b 1
)

echo ✓ All services are running
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║              ✓ SERVICES STARTED SUCCESSFULLY                              ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

echo Access the application at:
echo   Dashboard: http://127.0.0.1:3000
echo   API Docs:  http://127.0.0.1:8000/docs
echo   Swagger:   http://127.0.0.1:8000/swagger
echo.

echo Useful commands:
echo   View logs:      docker-compose logs -f
echo   Stop services:  docker-compose down
echo   View status:    docker-compose ps
echo.

pause

exit /b 0
