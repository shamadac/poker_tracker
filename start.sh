#!/bin/bash
# Startup script for MacOS

echo "🃏 Starting Poker Analyzer..."
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama is not running!"
    echo "Please start Ollama first:"
    echo "  1. Open Ollama app"
    echo "  2. Or run: ollama serve"
    echo ""
    exit 1
fi

echo "✓ Ollama is running"
echo ""

# Check if dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "🌐 Starting web server..."
echo "Open Chrome and go to: http://localhost:5000"
echo ""

python3 app.py
