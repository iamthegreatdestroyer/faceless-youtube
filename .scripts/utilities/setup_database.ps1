# ============================================================================
# FACELESS YOUTUBE - DATABASE SETUP WIZARD (PowerShell)
# ============================================================================
#
# This script runs the Python database setup wizard which will:
#   - Prompt for PostgreSQL credentials
#   - Create the database and user
#   - Update .env with connection string
#   - Run database migrations
#
# Usage: .\setup_database.ps1
#
# ============================================================================

param(
    [switch]$SkipVenvCheck = $false
)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  $Text" -ForegroundColor Cyan -NoNewline
    Write-Host ""
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "  ✓ $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "  ✗ $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "  ℹ $Text" -ForegroundColor Cyan
}

# Set up error handling
$ErrorActionPreference = "Stop"
trap {
    Write-Error $_
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Print header
Write-Host ""
Write-Header "FACELESS YOUTUBE - DATABASE SETUP WIZARD"
Write-Host "This will guide you through setting up PostgreSQL for local development" -ForegroundColor White
Write-Host ""

# Get project root (script location is .scripts/utilities/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Info "Project root: $ProjectRoot"

# Check if venv exists
$VenvPath = Join-Path $ProjectRoot "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

if (-not $SkipVenvCheck -and -not (Test-Path $PythonExe)) {
    Write-Error "Python virtual environment not found at $VenvPath"
    Write-Info "Please run: python -m venv venv"
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Success "Virtual environment found"

# Activate venv
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
Write-Info "Activating virtual environment..."

try {
    & $ActivateScript
    Write-Success "Virtual environment activated"
}
catch {
    Write-Error "Failed to activate virtual environment"
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Run setup script
Write-Host ""
Write-Info "Running database setup wizard..."
Write-Host ""

$SetupScript = Join-Path $ScriptDir "setup_database.py"

try {
    & $PythonExe $SetupScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Setup script failed with exit code $LASTEXITCODE"
        Write-Host ""
        Write-Host "Press any key to exit..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        exit 1
    }
}
catch {
    Write-Error "Failed to run setup script: $_"
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Success message
Write-Header "DATABASE SETUP COMPLETE!"
Write-Success "Your .env file has been updated with database connection details"
Write-Host ""
Write-Host "  Next, you can start the services:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. API Server (in PowerShell/CMD):" -ForegroundColor White
Write-Host "     uvicorn src.api.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Dashboard (in separate terminal):" -ForegroundColor White
Write-Host "     cd dashboard && npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
