# Windows Setup Guide

## Quick Start for Windows Users

### Step 1: Install Python
1. Download Python 3.8+ from: https://www.python.org/downloads/
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Verify: Open Command Prompt and type `python --version`

### Step 2: Install Ollama
1. Download from: https://ollama.ai/download
2. Install and run Ollama
3. Verify: Type `ollama --version` in Command Prompt

### Step 3: Run the Installer
1. Double-click `install_windows.bat`
2. Wait for it to download the AI model (~5 GB)
3. Wait for Python packages to install

### Step 4: Start the App
1. Double-click `start_windows.bat`
2. Open browser to: http://localhost:5001
3. Done!

## PokerStars Setup (Windows)

1. Open PokerStars
2. Go to: **Settings → Playing History → Hand History**
3. Check "**Save My Hand History**"
4. Click **Apply**

The app will automatically find your hand histories at:
`C:\Users\YourName\AppData\Local\PokerStars\HandHistory\`

## Troubleshooting

### "Python is not recognized"
- Reinstall Python and check "Add Python to PATH"
- Or add manually: System Properties → Environment Variables → Path

### "Ollama is not running"
- Open Ollama app from Start Menu
- Or run: `ollama serve` in Command Prompt

### "Port 5001 already in use"
- Edit `app.py` and change port to 5002 or 5003
- Look for: `app.run(debug=True, host='0.0.0.0', port=5001)`

### "No hands found"
- Make sure PokerStars hand history is enabled
- Check: `%LOCALAPPDATA%\PokerStars\HandHistory\`
- Or manually place .txt files in `hand_histories` folder

## Sharing with Friends

To share this app with a friend:
1. Zip the entire folder
2. Send to friend
3. Friend runs `install_windows.bat`
4. Friend runs `start_windows.bat`

That's it!
