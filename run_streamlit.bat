@echo off
echo Starting CMV Trading Bot Streamlit Frontend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade requirements
echo Installing requirements...
pip install -r streamlit_requirements.txt

REM Start the backend (if not already running)
echo.
echo Note: Make sure your FastAPI backend is running on http://localhost:8000
echo You can start it with: python -m uvicorn backend.app:app --reload
echo.

REM Start Streamlit
echo Starting Streamlit application...
echo Open your browser to: http://localhost:8501
echo.
streamlit run streamlit_enhanced.py

pause
