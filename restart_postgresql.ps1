# Restart PostgreSQL Service
# Requires Administrator privileges

# Check if running as Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Stopping PostgreSQL service..." -ForegroundColor Cyan
net stop postgresql-x64-14

Write-Host "Waiting 3 seconds..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

Write-Host "Starting PostgreSQL service..." -ForegroundColor Cyan
net start postgresql-x64-14

Write-Host "Waiting 5 seconds for PostgreSQL to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "Testing connection..." -ForegroundColor Cyan
psql -U postgres -h 127.0.0.1 -c "SELECT 1;" -q

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PostgreSQL is running and accepting connections!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run the setup script:" -ForegroundColor Yellow
    Write-Host ".\.scripts\utilities\setup_database.ps1" -ForegroundColor White
}
else {
    Write-Host "✗ PostgreSQL is still not responding. There may be a configuration issue." -ForegroundColor Red
}
