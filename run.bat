@echo off
setlocal

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup_venv.bat first.
    exit /b 1
)

:: Activate venv and run
call venv\Scripts\activate.bat
python -m src.main %*
set EXIT_CODE=%errorlevel%

:: Deactivate handled automatically when batch ends
exit /b %EXIT_CODE%
