# Poker Skill Development App

An AI-powered poker hand analyzer with beautiful visualizations and comprehensive playstyle evaluation. Uses Ollama for local AI analysis of PokerStars hand histories.

## ✨ Features

- 🌐 **Beautiful Web Interface** - Clean, modern UI with card graphics
- 🎴 **Visual Hand Replayer** - See cards, bets, and action with nice graphics
- 📊 **Comprehensive Stats** - VPIP, PFR, aggression factor, win rate
- 🤖 **AI Coach** - Personalized recommendations from Ollama
- 🔍 **Auto-Detection** - Finds PokerStars files automatically on MacOS
- 📈 **Playstyle Analysis** - Detailed evaluation of strengths and weaknesses
- 🎯 **Actionable Advice** - Specific improvement plan tailored to your game

## 🚀 Quick Start (MacOS)

### One-Click Installation

1. Download this repository (Download ZIP from GitHub)
2. Extract the ZIP file
3. Double-click `install_and_run.command`
4. Follow the prompts
5. Your browser will open automatically!

That's it! The installer handles everything:
- Checks for Python 3
- Installs/checks Ollama
- Downloads the AI model (llama2)
- Installs all dependencies
- Starts the web server
- Opens your browser

### Manual Installation

If you prefer manual setup:

```bash
# 1. Install Ollama
# Download from: https://ollama.ai/download

# 2. Pull AI model
ollama pull llama2

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Start the app
python3 app.py

# 5. Open browser
# Go to: http://localhost:5000
```

## 🎮 How to Use

### Setup PokerStars (One Time)
1. Open PokerStars
2. Go to: **Settings → Playing History → Hand History**
3. Check "**Save My Hand History**"
4. Click **Apply**

### Analyze Your Game
1. Play some poker on PokerStars
2. Open the Poker Analyzer in your browser
3. Click "**Scan for Hand Histories**" - automatically finds your files
4. Click "**Analyze Hands & Generate Report**"
5. Get comprehensive insights:
   - Overall playstyle statistics
   - Strengths and weaknesses
   - Hand-by-hand AI analysis
   - Visual hand replayer
   - Specific improvement recommendations

## 📊 What You'll Learn

### Statistics Tracked
- **VPIP** - How often you voluntarily put money in the pot
- **PFR** - How often you raise pre-flop
- **Aggression Factor** - Ratio of aggressive to passive actions
- **Win Rate** - Your winning percentage
- **Position Analysis** - Performance by position

### AI Analysis Includes
- Overall assessment of your playstyle
- Key strengths to leverage
- Critical weaknesses to fix
- Top 3 immediate improvements
- Long-term development plan
- Hand-by-hand strategic advice

### Visual Features
- Playing cards with suits and ranks
- Community cards by street (flop, turn, river)
- Betting action timeline
- Pot size tracking
- Showdown results
- Player stacks and positions

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "player_username": "Z420909",
  "ollama_model": "llama2",
  "ollama_url": "http://localhost:11434"
}
```

You can use different Ollama models:
- `llama2` (default, good balance)
- `mistral` (faster, lighter)
- `llama3` (more advanced)

## 📁 File Structure

```
poker-analyzer/
├── install_and_run.command  # One-click installer (MacOS)
├── app.py                    # Flask web server
├── hand_parser.py            # PokerStars format parser
├── ollama_analyzer.py        # AI analysis engine
├── playstyle_analyzer.py     # Statistics calculator
├── file_watcher.py           # Auto-detect hand histories
├── config.json               # Configuration
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Web interface
└── static/
    ├── style.css            # Main styles
    ├── cards.css            # Card graphics
    ├── app.js               # UI logic
    └── cards.js             # Card rendering
```

## 🔒 Privacy

- All analysis happens **locally** on your Mac
- No data is sent to external servers
- Your hand histories stay private
- Ollama runs completely offline

## 🐛 Troubleshooting

**"Ollama not connected"**
- Make sure Ollama is running: `ollama serve`
- Or open the Ollama app

**"No hands found"**
- Play some hands on PokerStars first
- Verify hand history saving is enabled in PokerStars
- Check: `~/Library/Application Support/PokerStars/HandHistory/`

**Analysis is slow**
- First analysis takes longer (model loading)
- Subsequent analyses are faster
- Consider using a lighter model like `mistral`

**Port 5000 already in use**
- Another app is using port 5000
- Edit `app.py` and change the port number

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

MIT License - feel free to use and modify!
