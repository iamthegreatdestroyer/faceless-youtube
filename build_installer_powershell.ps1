# Faceless YouTube - Installer Builder (PowerShell Version)
# This script builds the Windows installer using Inno Setup

param(
    [switch]$SkipBuild = $false
)

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "║     FACELESS YOUTUBE - WINDOWS INSTALLER BUILDER              ║" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Set script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Add Inno Setup to PATH
$env:Path += ';C:\Program Files (x86)\Inno Setup 6'

# ============================================================================
# Verification Functions
# ============================================================================

function Test-Prerequisite {
    param([string]$Name, [string]$TestCommand)
    
    Write-Host "Checking for $Name..." -ForegroundColor Yellow
    
    $result = Invoke-Expression $TestCommand -ErrorAction SilentlyContinue
    
    if ($result) {
        Write-Host "  ✅ $Name found" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "  ❌ $Name NOT found" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# Main Build Process
# ============================================================================

Write-Host "PREREQUISITES CHECK" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Cyan

# 1. Check Inno Setup
$isccPath = "C:\Program Files (x86)\Inno Setup 6\iscc.exe"
if (-not (Test-Path $isccPath)) {
    Write-Host "  ❌ Inno Setup NOT found at: $isccPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Inno Setup from: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
    exit 1
}
Write-Host "  ✅ Inno Setup found at: $isccPath" -ForegroundColor Green
Write-Host ""

# 2. Check executable
Write-Host "Checking for executable..." -ForegroundColor Yellow
if (Test-Path "dist\faceless-youtube.exe") {
    $exeSize = (Get-Item "dist\faceless-youtube.exe").Length / 1MB
    Write-Host "  ✅ Executable found: dist\faceless-youtube.exe ($([Math]::Round($exeSize, 2)) MB)" -ForegroundColor Green
}
else {
    Write-Host "  ❌ Executable NOT found: dist\faceless-youtube.exe" -ForegroundColor Red
    Write-Host "  Please run: pyinstaller --noconfirm build_minimal.spec" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 3. Check installer script
Write-Host "Checking for installer script..." -ForegroundColor Yellow
if (Test-Path "faceless-youtube.iss") {
    Write-Host "  ✅ Installer script found: faceless-youtube.iss" -ForegroundColor Green
}
else {
    Write-Host "  ❌ Installer script NOT found: faceless-youtube.iss" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 4. Check LICENSE
Write-Host "Checking for LICENSE file..." -ForegroundColor Yellow
if (-not (Test-Path "LICENSE")) {
    Write-Host "  ⚠️  LICENSE not found, creating default MIT License..." -ForegroundColor Yellow
    $licenseContent = @"
MIT License

Copyright (c) 2025 Faceless YouTube Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@
    $licenseContent | Out-File -FilePath LICENSE -Encoding UTF8
    Write-Host "  ✅ LICENSE created" -ForegroundColor Green
}
else {
    Write-Host "  ✅ LICENSE found" -ForegroundColor Green
}
Write-Host ""

# 5. Prepare output directory
Write-Host "Preparing output directory..." -ForegroundColor Yellow
if (Test-Path "Output") {
    Remove-Item -Path Output -Recurse -Force
    Write-Host "  ✅ Output directory cleaned" -ForegroundColor Green
}
New-Item -Path Output -ItemType Directory | Out-Null
Write-Host "  ✅ Output directory created" -ForegroundColor Green
Write-Host ""

if ($SkipBuild) {
    Write-Host "⏭️  Build skipped (use -SkipBuild flag to skip)" -ForegroundColor Yellow
    exit 0
}

# ============================================================================
# Build Phase
# ============================================================================

Write-Host "BUILD PHASE" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running Inno Setup compiler..." -ForegroundColor Yellow
Write-Host "Command: $isccPath /O`"Output`" faceless-youtube.iss" -ForegroundColor Cyan
Write-Host ""

& $isccPath /O"Output" faceless-youtube.iss

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Installer build FAILED with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Installer build completed successfully!" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Verification Phase
# ============================================================================

Write-Host "VERIFICATION PHASE" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""

# Verify installer was created
if (Test-Path "Output\faceless-youtube-setup.exe") {
    $installerSize = (Get-Item "Output\faceless-youtube-setup.exe").Length / 1MB
    Write-Host "✅ Installer file created:" -ForegroundColor Green
    Write-Host "   File: Output\faceless-youtube-setup.exe" -ForegroundColor Cyan
    Write-Host "   Size: $([Math]::Round($installerSize, 2)) MB" -ForegroundColor Cyan
}
else {
    Write-Host "❌ Installer file NOT created!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ============================================================================
# Completion
# ============================================================================

Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║          🎉 INSTALLER BUILD COMPLETE 🎉                      ║" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "║           Ready for End-User Distribution!                    ║" -ForegroundColor Green
Write-Host "║                                                                ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📦 INSTALLER DETAILS:" -ForegroundColor Yellow
Write-Host "   Location: Output\faceless-youtube-setup.exe" -ForegroundColor Cyan
Write-Host "   Size: $([Math]::Round($installerSize, 2)) MB" -ForegroundColor Cyan
Write-Host ""

Write-Host "🚀 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "   1. Share Output\faceless-youtube-setup.exe with users" -ForegroundColor Cyan
Write-Host "   2. Users double-click installer to run" -ForegroundColor Cyan
Write-Host "   3. Installation wizard guides the process" -ForegroundColor Cyan
Write-Host "   4. Application is ready to use" -ForegroundColor Cyan
Write-Host ""

Write-Host "✨ Distribution Ready!" -ForegroundColor Green
Write-Host ""
