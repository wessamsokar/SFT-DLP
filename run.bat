@echo off
echo Starting SFT-DLP...
cd /d "%~dp0"

REM Check if virtual environment exists and activate it
IF EXIST ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the application
python scripts\run_app.py

REM Pause if there was an error so the window doesn't close immediately
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
