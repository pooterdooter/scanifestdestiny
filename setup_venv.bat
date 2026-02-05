@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   PDF Scan Organizer - Setup
echo ============================================
echo.

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

:: Display Python version
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo Found: %%i

:: Check for existing venv
if exist "venv" (
    echo.
    echo [INFO] Virtual environment already exists.
    set /p REBUILD="Rebuild it? (y/N): "
    if /i "!REBUILD!"=="y" (
        echo Removing old venv...
        rmdir /s /q venv
    ) else (
        echo Skipping venv creation.
        goto :install_deps
    )
)

:: Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment created.

:install_deps
:: Activate and install dependencies
echo.
echo Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.

:: Check Tesseract installation
echo.
echo Checking Tesseract OCR...
where tesseract >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Tesseract OCR not found in PATH.
    echo.
    echo Please install Tesseract:
    echo   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo   2. Install and add to PATH (e.g., C:\Program Files\Tesseract-OCR)
    echo   3. Restart your terminal after installation
    echo.
    echo The tool will still work for text-based PDFs without Tesseract.
) else (
    for /f "tokens=*" %%i in ('tesseract --version 2^>^&1 ^| findstr /r "^tesseract"') do echo [OK] Found: %%i
)

:: Check Claude CLI
echo.
echo Checking Claude Code CLI...
where claude >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Claude Code CLI not found in PATH.
    echo Please ensure Claude Code is installed and accessible.
) else (
    echo [OK] Claude Code CLI found.
)

:: Create data directories if missing
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo Run 'run.bat --help' to see available commands.
echo.
pause
