#!/bin/bash
# One-click installer and launcher for MacOS
# Double-click this file to install everything and start the app

cd "$(dirname "$0")"

echo "🃏 Poker Skill Analyzer - Setup & Launch"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo ""
    echo "Please install Python 3 from:"
    echo "https://www.python.org/downloads/"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✓ Python 3 found"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "⚠️  Ollama is not installed!"
    echo ""
    echo "Ollama is required for AI analysis."
    echo "Would you like to:"
    echo "  1. Install Ollama now (recommended)"
    echo "  2. Continue without Ollama (app will run but analysis won't work)"
    echo "  3. Exit and install manually"
    echo ""
    read -p "Enter choice (1/2/3): " choice
    
    case $choice in
        1)
            echo ""
            echo "Opening Ollama download page..."
            open "https://ollama.ai/download"
            echo ""
            echo "After installing Ollama:"
            echo "  1. Open Terminal"
            echo "  2. Run: ollama pull llama2"
            echo "  3. Run this installer again"
            echo ""
            read -p "Press Enter to exit..."
            exit 0
            ;;
        2)
            echo ""
            echo "⚠️  Continuing without Ollama..."
            echo "You can install it later from: https://ollama.ai/download"
            ;;
        3)
            echo ""
            echo "Install Ollama from: https://ollama.ai/download"
            echo "Then run: ollama pull llama2"
            echo ""
            read -p "Press Enter to exit..."
            exit 0
            ;;
    esac
else
    echo "✓ Ollama found"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running"
    else
        echo ""
        echo "Starting Ollama..."
        ollama serve > /dev/null 2>&1 &
        sleep 2
        
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "✓ Ollama started successfully"
        else
            echo "⚠️  Could not start Ollama automatically"
            echo "Please open Ollama app or run: ollama serve"
        fi
    fi
    
    # Check if llama2 model is installed
    if ollama list | grep -q "llama2"; then
        echo "✓ llama2 model installed"
    else
        echo ""
        echo "📥 Downloading llama2 model (this may take a few minutes)..."
        ollama pull llama2
        
        if [ $? -eq 0 ]; then
            echo "✓ llama2 model installed successfully"
        else
            echo "⚠️  Failed to download llama2 model"
            echo "You can try manually: ollama pull llama2"
        fi
    fi
fi

echo ""
echo "📦 Installing Python dependencies..."

# Install pip packages
if pip3 install -r requirements.txt > /dev/null 2>&1; then
    echo "✓ Dependencies installed"
else
    echo "⚠️  Some dependencies may have failed to install"
    echo "Trying alternative method..."
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "🎮 Checking PokerStars hand history settings..."
echo ""
echo "Make sure PokerStars is configured to save hand histories:"
echo "  1. Open PokerStars"
echo "  2. Settings → Playing History → Hand History"
echo "  3. Check 'Save My Hand History'"
echo "  4. Click Apply"
echo ""

read -p "Press Enter when ready to start the app..."

echo ""
echo "🚀 Starting Poker Analyzer..."
echo ""
echo "The app will open in your browser at:"
echo "http://localhost:5000"
echo ""
echo "To stop the app, close this window or press Ctrl+C"
echo ""

# Open browser after a short delay
(sleep 3 && open "http://localhost:5000") &

# Start the Flask app
python3 app.py
