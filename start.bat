@echo off
echo MySQL Database Transfer Tool
echo ==========================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
if not exist "venv\Lib\site-packages\flask" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if config file exists
if not exist "config.json" (
    echo.
    echo WARNING: config.json not found!
    echo Please copy config.json.template to config.json and update with your database settings
    echo.
    pause
)

REM Start the application
echo Starting MySQL Database Transfer Tool...
echo Open your browser and navigate to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python app.py

pause
