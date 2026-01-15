# Quick Setup Guide for MacOS

## 🚀 Super Easy Setup (Recommended)

1. **Download** this repository as a ZIP file from GitHub
2. **Extract** the ZIP file to your Desktop or Documents
3. **Double-click** `install_and_run.command`
4. **Follow** the prompts in the terminal window
5. **Done!** Your browser opens automatically

The installer does everything for you:
- ✅ Checks Python installation
- ✅ Installs/verifies Ollama
- ✅ Downloads AI model (llama2)
- ✅ Installs all dependencies
- ✅ Starts the web server
- ✅ Opens Chrome automatically

## 🎮 Using the App

### First Time Setup (2 minutes)

**Enable PokerStars Hand History:**
1. Open PokerStars
2. Click Settings (⚙️ gear icon)
3. Go to: **Playing History** → **Hand History**
4. Check "**Save My Hand History**"
5. Click **Apply**

### Every Time You Want to Analyze

1. **Play poker** on PokerStars (or use existing hand histories)
2. **Double-click** `install_and_run.command` (or go to http://localhost:5000 if already running)
3. **Click** "Scan for Hand Histories"
4. **Click** "Analyze Hands & Generate Report"
5. **Read** your comprehensive analysis!

## 📊 What You Get

### Comprehensive Playstyle Report
- **VPIP** - How often you play hands
- **PFR** - How aggressive you are pre-flop
- **Aggression Factor** - Your betting style
- **Win Rate** - Your success percentage
- **Strengths** - What you're doing well
- **Weaknesses** - What needs improvement

### Individual Hand Analysis
- AI coach feedback on each hand
- Visual card display with suits
- Complete betting action timeline
- Board cards (flop, turn, river)
- Pot size and player stacks
- Showdown results
- Specific strategic advice

### Overall Recommendations
- Top 3 things to improve immediately
- Long-term development plan
- Specific actions to take
- Expected impact on your game

## 💡 Tips

- **Start small**: Analyze 5 hands first (takes ~2 minutes)
- **Be patient**: First analysis is slower (loading AI model)
- **Review regularly**: Analyze after each session to track improvement
- **Read carefully**: The AI provides specific, actionable advice
- **Expand details**: Click "Show Full Hand History" to see complete action

## 🔧 Troubleshooting

### "Ollama not connected"
**Solution**: The installer should handle this, but if you see this:
```bash
ollama serve
```
Or just open the Ollama app from Applications

### "No hands found"
**Solutions**:
1. Make sure you've played some hands on PokerStars
2. Verify hand history is enabled (see setup above)
3. Check this folder exists: `~/Library/Application Support/PokerStars/HandHistory/`
4. You can manually place .txt hand history files in the `hand_histories/` folder

### "Python not found"
**Solution**: Install Python 3 from https://www.python.org/downloads/

### App won't start
**Solution**: Open Terminal and run:
```bash
cd /path/to/poker-analyzer
python3 app.py
```

### Analysis is very slow
**Solutions**:
- First analysis is always slower (loading model)
- Subsequent analyses are much faster
- Try analyzing fewer hands (3-5 instead of 10-20)
- Consider using a faster model: Edit `config.json` and change `"ollama_model": "mistral"`

## 🎯 Getting the Most Value

1. **Analyze regularly** - After each session while hands are fresh in your mind
2. **Focus on mistakes** - Pay special attention to the "Areas for Improvement" section
3. **Implement one thing** - Pick one recommendation and focus on it for your next session
4. **Track progress** - Keep notes on what you're working on
5. **Review patterns** - Look for recurring mistakes across multiple analyses

## 🔒 Privacy Note

Everything runs **locally on your Mac**:
- No internet connection required (after initial setup)
- Your hand histories never leave your computer
- Ollama AI runs completely offline
- Your poker data stays 100% private

## ❓ Questions?

- Check the main README.md for more details
- Make sure Ollama is running: `ollama list` should show llama2
- Verify PokerStars is saving files: Check `~/Library/Application Support/PokerStars/HandHistory/`
- Try the manual installation steps if the one-click installer has issues
