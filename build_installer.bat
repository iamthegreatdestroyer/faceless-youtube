@echo off
REM ============================================================================
REM Faceless YouTube - Installer Builder Script
REM Creates professional Windows installer using Inno Setup
REM ============================================================================

setlocal enabledelayedexpansion

REM Colors (using echo with special characters)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "CYAN=[94m"
set "RESET=[0m"

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM ============================================================================
REM Helper Functions
REM ============================================================================

:print_header
    echo.
    echo ==============================================================================
    echo.   %~1
    echo ==============================================================================
    echo.
    exit /b 0

:print_success
    echo [SUCCESS] %~1
    exit /b 0

:print_error
    echo [ERROR] %~1
    exit /b 1

:print_info
    echo [INFO] %~1
    exit /b 0

REM ============================================================================
REM Main Script
REM ============================================================================

call :print_header "FACELESS YOUTUBE - INSTALLER BUILDER"

REM Check prerequisites
echo Checking prerequisites...

REM 1. Check for Inno Setup installation
echo.
echo Checking for Inno Setup...
where iscc.exe >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Inno Setup is not installed or not in PATH
    echo.
    echo Please install Inno Setup from: https://jrsoftware.org/isdl.php
    echo After installation, either:
    echo   1. Add Inno Setup to your PATH environment variable
    echo   2. Or specify the path below:
    echo.
    set /p INNO_PATH="Enter path to Inno Setup (or press Enter to skip): "
    if not "!INNO_PATH!"=="" (
        if exist "!INNO_PATH!\iscc.exe" (
            set "iscc=!INNO_PATH!\iscc.exe"
        ) else (
            call :print_error "Inno Setup not found at !INNO_PATH!"
            exit /b 1
        )
    ) else (
        call :print_error "Inno Setup is required to build the installer"
        exit /b 1
    )
) else (
    set "iscc=iscc.exe"
    echo [SUCCESS] Inno Setup found
)

REM 2. Check for executable
echo.
echo Checking for executable...
if not exist "dist\faceless-youtube\faceless-youtube.exe" (
    call :print_error "Executable not found: dist\faceless-youtube\faceless-youtube.exe"
    echo Please run: pyinstaller --noconfirm build_minimal.spec
    exit /b 1
)
echo [SUCCESS] Executable found

REM 3. Check for installer script
echo.
echo Checking for installer script...
if not exist "faceless-youtube.iss" (
    call :print_error "Installer script not found: faceless-youtube.iss"
    exit /b 1
)
echo [SUCCESS] Installer script found

REM 4. Check for LICENSE file
echo.
echo Checking for LICENSE file...
if not exist "LICENSE" (
    echo [WARNING] LICENSE file not found, creating default...
    (
        echo MIT License
        echo.
        echo Copyright ^(c^) 2025 Faceless YouTube Project
        echo.
        echo Permission is hereby granted, free of charge, to any person obtaining a copy
        echo of this software and associated documentation files ^(the "Software"^), to deal
        echo in the Software without restriction, including without limitation the rights
        echo to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        echo copies of the Software, and to permit persons to whom the Software is
        echo furnished to do so, subject to the following conditions:
        echo.
        echo The above copyright notice and this permission notice shall be included in all
        echo copies or substantial portions of the Software.
    ) > LICENSE
    echo [SUCCESS] Default LICENSE created
) else (
    echo [SUCCESS] LICENSE file found
)

REM Clean output directory
echo.
echo Cleaning output directory...
if exist "Output" (
    rmdir /s /q Output 2>nul
)
mkdir Output
echo [SUCCESS] Output directory prepared

REM Run Inno Setup compiler
echo.
call :print_header "BUILDING INSTALLER"
echo.
echo Running Inno Setup compiler...
echo Command: %iscc% /O"Output" faceless-youtube.iss
echo.

%iscc% /O"Output" faceless-youtube.iss
if errorlevel 1 (
    call :print_error "Installer build failed"
    exit /b 1
)

echo.
echo [SUCCESS] Installer build completed successfully

REM Verify output
echo.
echo Verifying installer...
if not exist "Output\faceless-youtube-setup.exe" (
    call :print_error "Installer file not created"
    exit /b 1
)

REM Get file size
for /F "tokens=*" %%A in ('powershell -Command "("{0:F2} MB" -f ((Get-Item 'Output\faceless-youtube-setup.exe').Length / 1MB))"') do (
    set "INSTALLER_SIZE=%%A"
)

echo [SUCCESS] Installer created: Output\faceless-youtube-setup.exe
echo [INFO] Size: %INSTALLER_SIZE%

REM Success message
call :print_header "INSTALLER BUILD COMPLETE"
echo.
echo Installer Details:
echo   File: Output\faceless-youtube-setup.exe
echo   Size: %INSTALLER_SIZE%
echo.
echo Installation Instructions:
echo   1. Double-click faceless-youtube-setup.exe
echo   2. Follow the installation wizard
echo   3. Choose installation directory ^(default: C:\Program Files\Faceless YouTube\^)
echo   4. Select additional options ^(desktop shortcut, etc.^)
echo   5. Complete the installation
echo   6. The application will launch automatically ^(optional^)
echo.
echo The installer is ready for distribution!
echo.

exit /b 0
