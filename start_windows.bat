@echo off
REM Start Poker Analyzer on Windows

echo ========================================
echo    Poker Analyzer - Starting...
echo ========================================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [INFO] Starting Ollama...
    start /B ollama serve
    timeout /t 3 >nul
)

echo [INFO] Starting Poker Analyzer...
echo.
echo Open your browser to: http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

python app.py
