@echo off
REM Start the app with virtual environment (Windows)

echo ========================================
echo    Poker Analyzer - Starting...
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   setup_venv.bat
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [INFO] Starting Ollama...
    start /B ollama serve
    timeout /t 3 >nul
)

echo [OK] Virtual environment activated
echo [OK] Starting server...
echo.
echo Open your browser to: http://localhost:5001
echo.
echo Press Ctrl+C to stop
echo.

REM Start the app
python app.py
