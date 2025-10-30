#!/usr/bin/env pwsh
# Quick Start Script for Faceless YouTube API

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗"
Write-Host "║  FACELESS YOUTUBE - QUICK START                               ║"
Write-Host "╚════════════════════════════════════════════════════════════════╝"
Write-Host ""

# Get project root
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommandPath
if (-not $ProjectRoot) {
    $ProjectRoot = Get-Location
}

Write-Host "📍 Project Root: $ProjectRoot"
Write-Host ""

# Check virtual environment
if (-not (Test-Path "$ProjectRoot\venv\Scripts\Activate.ps1")) {
    Write-Host "✗ Virtual environment not found"
    Write-Host "  Run: python -m venv venv"
    exit 1
}

# Activate virtual environment
Write-Host "🐍 Activating virtual environment..."
& "$ProjectRoot\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated"
Write-Host ""

# Check database
Write-Host "🔍 Checking database connection..."
$env:PGPASSWORD = 'FacelessYT2025!'
$result = psql -U faceless_youtube -d faceless_youtube -h localhost -p 5433 -c "SELECT 1;" 2>&1 | Select-String "1"
if ($result) {
    Write-Host "✓ Database connected"
}
else {
    Write-Host "⚠ Database check failed - ensure PostgreSQL is running"
}
Write-Host ""

# Display options
Write-Host "🚀 SELECT AN OPTION:"
Write-Host ""
Write-Host "  1. Start API Server (port 8000)"
Write-Host "  2. Start Dashboard (port 5173)"
Write-Host "  3. Run Tests"
Write-Host "  4. Start All Services"
Write-Host "  5. Exit"
Write-Host ""

$choice = Read-Host "Enter choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🚀 Starting API Server..."
        Write-Host "📍 Access: http://localhost:8000/docs"
        Write-Host ""
        uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    }
    "2" {
        Write-Host ""
        Write-Host "🚀 Starting Dashboard..."
        Write-Host "📍 Access: http://localhost:5173"
        Write-Host ""
        Set-Location "$ProjectRoot\dashboard"
        npm run dev
    }
    "3" {
        Write-Host ""
        Write-Host "🧪 Running Tests..."
        Write-Host ""
        pytest tests/unit/ -v --tb=short
    }
    "4" {
        Write-Host ""
        Write-Host "🚀 Starting All Services..."
        Write-Host ""
        Write-Host "Open 3 new terminals and run:"
        Write-Host ""
        Write-Host "Terminal 1 (API):"
        Write-Host "  cd $ProjectRoot"
        Write-Host "  .\venv\Scripts\Activate.ps1"
        Write-Host "  uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
        Write-Host ""
        Write-Host "Terminal 2 (Dashboard):"
        Write-Host "  cd $ProjectRoot\dashboard"
        Write-Host "  npm run dev"
        Write-Host ""
        Write-Host "Terminal 3 (Worker - Optional):"
        Write-Host "  cd $ProjectRoot"
        Write-Host "  .\venv\Scripts\Activate.ps1"
        Write-Host "  celery -A src.services.background_jobs.celery_app worker -l info"
        Write-Host ""
    }
    "5" {
        Write-Host "✓ Goodbye!"
        exit 0
    }
    default {
        Write-Host "✗ Invalid choice"
        exit 1
    }
}

Write-Host ""
