#!/bin/bash
# Quick model switcher for Poker Analyzer

echo "🎰 Poker Analyzer - Model Switcher"
echo "=================================="
echo ""
echo "Current model: $(grep ollama_model config.json | cut -d'"' -f4)"
echo ""
echo "Available models on your system:"
ollama list
echo ""
echo "Recommended models for poker analysis:"
echo "  1. llama3.1:8b    - Best overall (4.7 GB)"
echo "  2. qwen2.5:7b     - Most intelligent (4.4 GB)"
echo "  3. llama3.2:3b    - Fastest (2 GB)"
echo "  4. gemma2:9b      - Best teacher (5.4 GB)"
echo ""
read -p "Enter model name to install/switch to (or press Enter to cancel): " model

if [ -z "$model" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "📥 Pulling model: $model"
ollama pull "$model"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Model downloaded successfully!"
    echo ""
    echo "📝 Updating config.json..."
    
    # Update config.json
    sed -i.bak "s/\"ollama_model\": \"[^\"]*\"/\"ollama_model\": \"$model\"/" config.json
    
    echo "✅ Config updated!"
    echo ""
    echo "🔄 Restart the app to use the new model."
    echo "   The server will auto-reload if it's running."
else
    echo ""
    echo "❌ Failed to download model."
    echo "   Check the model name and try again."
fi
