#!/bin/bash
# Start the app with virtual environment (macOS/Linux)

echo "🃏 Poker Analyzer - Starting..."
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please run setup first:"
    echo "  ./setup_venv.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running"
    echo "Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

echo "✓ Virtual environment activated"
echo "✓ Starting server..."
echo ""
echo "🌐 Open your browser to: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the app
python app.py
