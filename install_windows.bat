@echo off
REM Windows installer for Poker Analyzer
echo ========================================
echo    Poker Analyzer - Windows Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not installed!
    echo.
    echo Ollama is required for AI analysis.
    echo.
    echo Please install from: https://ollama.ai/download
    echo.
    echo After installing Ollama:
    echo   1. Open Command Prompt
    echo   2. Run: ollama pull llama3.1:8b
    echo   3. Run this installer again
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama found
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [INFO] Starting Ollama...
    start /B ollama serve
    timeout /t 3 >nul
)

REM Check for llama3.1:8b model
ollama list | findstr "llama3.1:8b" >nul
if errorlevel 1 (
    echo [INFO] Downloading llama3.1:8b model (this may take a few minutes)...
    ollama pull llama3.1:8b
) else (
    echo [OK] llama3.1:8b model found
)

echo.
echo [INFO] Installing Python dependencies...
pip install -r requirements.txt

echo.
echo [INFO] Creating virtual environment...
python -m venv .venv

if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [INFO] Installing dependencies in virtual environment...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo To start the app, run: start_windows.bat
echo.
pause
