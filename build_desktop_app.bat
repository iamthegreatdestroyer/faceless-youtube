@echo off
REM Faceless YouTube - Desktop Application Builder (Windows)
REM =======================================================
REM
REM This script builds the PyQt6 desktop application into a standalone Windows executable
REM using PyInstaller. Handles venv activation, dependency checking, and build process.
REM
REM Usage:
REM   build_desktop_app.bat              - Build with default settings
REM   build_desktop_app.bat --clean      - Clean build artifacts first
REM   build_desktop_app.bat --onefile    - Build as single executable
REM   build_desktop_app.bat --help       - Show help
REM
REM Requirements:
REM   - Python 3.13+
REM   - Virtual environment (venv) in project root
REM   - PyInstaller installed
REM
REM Output:
REM   - dist\faceless-youtube.exe (main executable)
REM   - dist\faceless-youtube\   (supporting files)
REM   - Size: 800MB - 1.2GB

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Color setup (ANSI codes)
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RED=[91m"
set "RESET=[0m"

REM Helper functions
goto :main

:print_header
    echo.
    echo %BLUE%======================================================================%RESET%
    echo %BLUE%  %~1%RESET%
    echo %BLUE%======================================================================%RESET%
    echo.
    exit /b 0

:print_success
    echo %GREEN%[OK]%RESET% %~1
    exit /b 0

:print_error
    echo %RED%[ERROR]%RESET% %~1
    exit /b 0

:print_warning
    echo %YELLOW%[WARN]%RESET% %~1
    exit /b 0

:print_info
    echo %BLUE%[INFO]%RESET% %~1
    exit /b 0

:main
    REM Check for help
    if "%~1"=="--help" goto :help
    if "%~1"=="-h" goto :help
    if "%~1"=="/?" goto :help

    call :print_header "FACELESS YOUTUBE - DESKTOP APP BUILDER"

    REM Parse arguments
    set "CLEAN_BUILD=0"
    set "ONEFILE=0"

    :parse_args
    if "%~1"=="" goto :args_done
    if "%~1"=="--clean" (
        set "CLEAN_BUILD=1"
        shift
        goto :parse_args
    )
    if "%~1"=="--onefile" (
        set "ONEFILE=1"
        shift
        goto :parse_args
    )
    if "%~1"=="--help" goto :help
    shift
    goto :parse_args

    :args_done
    REM Check Python
    call :print_info "Checking Python installation..."
    python --version >nul 2>&1
    if errorlevel 1 (
        call :print_error "Python not found. Please install Python 3.13+"
        exit /b 1
    )
    for /f "tokens=2" %%A in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%A"
    call :print_success "Python %PYTHON_VERSION% found"

    REM Check venv
    if not exist "venv\Scripts\activate.bat" (
        if not exist ".venv\Scripts\activate.bat" (
            call :print_error "Virtual environment not found at venv\ or .venv\"
            exit /b 1
        ) else (
            set "VENV_PATH=.venv"
        )
    ) else (
        set "VENV_PATH=venv"
    )

    REM Activate venv
    call :print_info "Activating virtual environment..."
    call "%VENV_PATH%\Scripts\activate.bat"
    call :print_success "Virtual environment activated"

    REM Check PyInstaller
    call :print_info "Checking PyInstaller installation..."
    python -c "import PyInstaller" >nul 2>&1
    if errorlevel 1 (
        call :print_warning "PyInstaller not found. Installing..."
        pip install PyInstaller
        call :print_success "PyInstaller installed"
    ) else (
        call :print_success "PyInstaller is installed"
    )

    REM Clean if requested
    if %CLEAN_BUILD% equ 1 (
        call :print_info "Cleaning build artifacts..."
        if exist "build" rmdir /s /q build
        if exist "dist" rmdir /s /q dist
        if exist "__pycache__" rmdir /s /q __pycache__
        call :print_success "Cleaned"
    )

    REM Check spec file
    if not exist "build_desktop_app.spec" (
        call :print_error "Spec file not found: build_desktop_app.spec"
        exit /b 1
    )

    call :print_info "Using spec file: build_desktop_app.spec"

    REM Build
    call :print_header "BUILDING EXECUTABLE"

    set "BUILD_ARGS=--noconfirm --clean"
    
    if %ONEFILE% equ 1 (
        call :print_info "Building as single file (this may take longer)..."
        set "BUILD_ARGS=!BUILD_ARGS! --onefile"
    ) else (
        call :print_info "Building with directory structure (faster)..."
    )

    echo Build command:
    echo   pyinstaller %BUILD_ARGS% build_desktop_app.spec
    echo.

    REM Run PyInstaller
    pyinstaller %BUILD_ARGS% build_desktop_app.spec
    if errorlevel 1 (
        call :print_error "Build failed. Check output above for details."
        exit /b 1
    )

    call :print_success "Build completed successfully!"

    echo.
    echo Output location:
    if exist "dist\faceless-youtube.exe" (
        for /f "tokens=*" %%A in ('dir /s/b "dist\faceless-youtube.exe"') do (
            echo   %%A
            call :print_success "Executable ready at: %%A"
        )
    )
    if exist "dist\faceless-youtube" (
        echo   dist\faceless-youtube\
        call :print_success "Application bundle ready at: dist\faceless-youtube\"
    )

    echo.
    echo Next steps:
    echo   1. Test the application:
    echo      dist\faceless-youtube.exe
    echo.
    echo   2. To create an installer, you can use NSIS or Inno Setup:
    echo      https://nsis.sourceforge.io
    echo      https://www.innosetup.com
    echo.

    call :print_header "BUILD COMPLETE"
    exit /b 0

    :help
    echo Faceless YouTube Desktop App Builder
    echo.
    echo Usage: build_desktop_app.bat [OPTIONS]
    echo.
    echo Options:
    echo   --clean     Remove build artifacts before building
    echo   --onefile   Build as single executable (slower, larger, but portable)
    echo   --help      Show this help message
    echo.
    echo Examples:
    echo   build_desktop_app.bat               - Build with default settings
    echo   build_desktop_app.bat --clean       - Clean build
    echo   build_desktop_app.bat --onefile     - Build as single file
    echo.
    echo Output:
    echo   dist\faceless-youtube.exe           - Main executable
    echo   dist\faceless-youtube\              - Supporting files
    echo.
    exit /b 0
