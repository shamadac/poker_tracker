@echo off
REM Setup virtual environment for Windows

echo ========================================
echo    Setting up Python Virtual Environment
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH"!
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Create virtual environment
echo [INFO] Creating virtual environment...
python -m venv .venv

if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment created
echo.

REM Activate and install dependencies
echo [INFO] Installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo [OK] Dependencies installed
echo.

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not installed!
    echo.
    echo Install from: https://ollama.ai/download
    echo.
) else (
    echo [OK] Ollama found
    
    REM Check if model is installed
    ollama list | findstr "llama3.1:8b" >nul
    if errorlevel 1 (
        echo [INFO] Downloading llama3.1:8b model...
        ollama pull llama3.1:8b
    ) else (
        echo [OK] llama3.1:8b model installed
    )
)

echo.
echo ==========================================
echo    Setup Complete!
echo ==========================================
echo.
echo To activate the virtual environment:
echo   .venv\Scripts\activate.bat
echo.
echo To start the app:
echo   .venv\Scripts\activate.bat
echo   python app.py
echo.
echo Or use the start script:
echo   start_venv.bat
echo.
pause
