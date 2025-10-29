# ============================================================================
# FACELESS YOUTUBE - AUTOMATIC DATABASE SETUP
# ============================================================================
# This script runs the database setup with pre-configured credentials
# No manual prompts needed!
# ============================================================================

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  FACELESS YOUTUBE - AUTOMATIC DATABASE SETUP                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Set environment variables for automatic setup
Write-Host "Setting up environment variables..." -ForegroundColor Yellow
$env:POSTGRES_ADMIN_USER = "postgres"
$env:POSTGRES_ADMIN_PASSWORD = "FacelessYT2025!"
$env:POSTGRES_PORT = "5433"
$env:POSTGRES_HOST = "localhost"

Write-Host "✓ PostgreSQL User: postgres" -ForegroundColor Green
Write-Host "✓ PostgreSQL Port: 5433" -ForegroundColor Green
Write-Host "✓ PostgreSQL Host: localhost" -ForegroundColor Green
Write-Host ""

# Navigate to project root
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Project root: $projectRoot" -ForegroundColor Cyan
Write-Host ""

# Activate venv if not already activated
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "✗ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Run the setup script with environment variables
Write-Host "Running database setup wizard..." -ForegroundColor Yellow
Write-Host "──────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""

python ".\.scripts\utilities\setup_database.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✓ DATABASE SETUP COMPLETE!                                  ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Verify: psql -U faceless_youtube -d faceless_youtube -h localhost -p 5433 -c 'SELECT 1;'" -ForegroundColor White
    Write-Host "2. Start API: uvicorn src.api.main:app --reload" -ForegroundColor White
    Write-Host "3. Start Dashboard: cd dashboard && npm run dev" -ForegroundColor White
    Write-Host ""
}
else {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  ✗ DATABASE SETUP FAILED                                      ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the output above for error details." -ForegroundColor Yellow
    exit 1
}
