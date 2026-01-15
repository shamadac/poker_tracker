#!/bin/bash
# Setup virtual environment for macOS/Linux

echo "🔧 Setting up Python Virtual Environment"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install from: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo ""

# Activate and install dependencies
echo "📥 Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama is not installed!"
    echo "Install from: https://ollama.ai/download"
    echo ""
else
    echo "✓ Ollama found"
    
    # Check if model is installed
    if ollama list | grep -q "llama3.1:8b"; then
        echo "✓ llama3.1:8b model installed"
    else
        echo "📥 Downloading llama3.1:8b model..."
        ollama pull llama3.1:8b
    fi
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To start the app:"
echo "  source .venv/bin/activate"
echo "  python app.py"
echo ""
echo "Or use the start script:"
echo "  ./start_venv.sh"
echo ""
