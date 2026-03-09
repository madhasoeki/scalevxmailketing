@echo off
echo ========================================
echo  ScaleV x Mailketing - Lead Management
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan!
    echo Silakan install Python terlebih dahulu.
    pause
    exit /b 1
)

echo [1/4] Checking dependencies...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing/Updating dependencies...
pip install -r requirements.txt --quiet

echo [4/4] Initializing database...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized!')"

echo.
echo ========================================
echo  Starting Application...
echo ========================================
echo.
echo  Dashboard: http://localhost:5000
echo  Settings:  http://localhost:5000/settings
echo.
echo  Press CTRL+C to stop
echo.

python app.py

pause
