# 🃏 Poker Skill Analyzer

An AI-powered poker hand analyzer with beautiful visualizations and comprehensive playstyle evaluation. Uses Ollama for local AI analysis of PokerStars hand histories.

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey)

## ✨ Features

### 🤖 AI-Powered Analysis
- **Beginner-Friendly Explanations** - No poker jargon without explanation
- **Personalized Coaching** - Based on YOUR playing style
- **Top 5 Strengths & Mistakes** - Clear, actionable feedback
- **Poker Concepts Explained** - Learn while you improve

### 📊 Interactive Dashboard
- **Statistics Overview** - VPIP, PFR, Aggression Factor, Win Rate
- **Hand History Table** - Searchable, filterable, color-coded
- **Play Money vs Real Money** - Separate tracking and analysis
- **Performance Breakdown** - Visual charts and graphs

### 📈 Graphs & Visualizations
- **Win Rate Over Time** - Track your improvement
- **VPIP & PFR Trends** - See your playing style evolution
- **Position Performance** - Which positions are profitable
- **Daily Performance** - Spot your best and worst sessions
- **Interactive Filters** - By game type, time period, stakes

### 🎯 Key Features
- ✅ Analyze ALL hands at once (not just 5)
- ✅ Progress monitoring during analysis
- ✅ Automatic PokerStars file detection
- ✅ Cross-platform (Windows + macOS)
- ✅ 100% local and private (no data sent to servers)
- ✅ Beautiful, responsive UI

## 🚀 Quick Start

### macOS

1. **Double-click** `install_and_run.command`
2. Follow the prompts
3. Browser opens automatically!

### Windows

1. **Double-click** `install_windows.bat`
2. Wait for installation
3. **Double-click** `start_windows.bat`
4. Open browser to http://localhost:5001

### Manual Installation

```bash
# 1. Install Ollama
# Download from: https://ollama.ai/download

# 2. Pull AI model
ollama pull llama3.1:8b

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Start the app
python3 app.py

# 5. Open browser
# Go to: http://localhost:5001
```

## 📋 Requirements

- **Python 3.8+**
- **Ollama** (for AI analysis)
- **PokerStars** (with hand history enabled)

### System Requirements
- **Minimum**: 8 GB RAM, 5 GB disk space
- **Recommended**: 16 GB RAM, 10 GB disk space

## 🎮 How to Use

### 1. Enable PokerStars Hand History
1. Open PokerStars
2. Go to: **Settings → Playing History → Hand History**
3. Check "**Save My Hand History**"
4. Click **Apply**

### 2. Analyze Your Game
1. Open http://localhost:5001
2. Click "**Scan for Hand Histories**"
3. Click "**Analyze All Hands (Summary Only)**"
4. Read your personalized analysis!

### 3. Explore Features
- **Dashboard** - View detailed statistics and hand history
- **Graphs** - Interactive charts showing your progress
- **Filters** - Separate play money from real money games

## 📊 What You'll Learn

### Statistics Tracked
- **VPIP** - How often you play hands
- **PFR** - How often you raise pre-flop
- **Aggression Factor** - Bet/raise vs call ratio
- **Win Rate** - Your winning percentage
- **Position Analysis** - Performance by table position

### AI Analysis Includes
- Your playing style (tight/loose, aggressive/passive)
- Top 5 strengths you're leveraging
- Top 5 mistakes costing you money
- Top 5 improvements to work on
- Poker concepts you need to learn
- Quick tips for your next session

## 🎨 Screenshots

### Main Analysis Page
- Beginner-friendly AI coaching
- Executive summary format
- Clear action items

### Dashboard
- Statistics overview cards
- Complete hand history table
- Search and filter functionality

### Graphs Page
- 6 interactive charts
- Multiple filter options
- Track improvement over time

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "player_username": "YourUsername",
  "ollama_model": "llama3.1:8b",
  "ollama_url": "http://localhost:11434"
}
```

### Recommended AI Models

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3.1:8b | 4.7 GB | Fast | Excellent | Most users ⭐ |
| qwen2.5:7b | 4.4 GB | Fast | Excellent | Deep analysis |
| llama3.2:3b | 2 GB | Very Fast | Good | Quick analysis |

See `RECOMMENDED_MODELS.md` for details.

## 📁 Project Structure

```
poker-analyzer/
├── app.py                    # Flask web server
├── hand_parser.py            # PokerStars format parser
├── ollama_analyzer.py        # AI analysis engine
├── playstyle_analyzer.py     # Statistics calculator
├── file_watcher.py           # Auto-detect hand histories
├── config.json               # Configuration
├── requirements.txt          # Python dependencies
├── templates/                # HTML pages
│   ├── index.html           # Main analysis page
│   ├── dashboard.html       # Statistics dashboard
│   └── graphs.html          # Interactive graphs
└── static/                   # CSS, JavaScript, assets
    ├── app.js
    ├── dashboard.js
    ├── graphs.js
    └── style.css
```

## 🔒 Privacy

- ✅ All analysis happens **locally** on your computer
- ✅ No data sent to external servers
- ✅ Your hand histories stay private
- ✅ Ollama runs completely offline
- ✅ 100% open source

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/poker-analyzer.git
cd poker-analyzer

# Install dependencies
pip3 install -r requirements.txt

# Run the app
python3 app.py
```

### Collaboration Guide
See `GITHUB_COLLABORATION_GUIDE.md` for detailed instructions on working together.

## 🐛 Troubleshooting

### "Ollama not connected"
- Make sure Ollama is running: `ollama serve`
- Or open the Ollama app

### "No hands found"
- Play some hands on PokerStars first
- Verify hand history saving is enabled
- Check: `~/Library/Application Support/PokerStars/HandHistory/` (macOS)
- Or: `%LOCALAPPDATA%\PokerStars\HandHistory\` (Windows)

### "Port 5001 already in use"
- Edit `app.py` and change the port number
- Look for: `app.run(debug=True, host='0.0.0.0', port=5001)`

### Windows Setup Issues
See `WINDOWS_SETUP.md` for detailed Windows troubleshooting.

## 📚 Documentation

- `README.md` - This file
- `SETUP_GUIDE.md` - Detailed setup instructions
- `FEATURES.md` - Complete feature list
- `RECOMMENDED_MODELS.md` - AI model recommendations
- `GITHUB_COLLABORATION_GUIDE.md` - How to collaborate
- `WINDOWS_SETUP.md` - Windows-specific setup
- `HAND_ADVISOR_PLAN.md` - Future feature planning

## 🗺️ Roadmap

### Current Version (2.0)
- ✅ Beginner-friendly AI analysis
- ✅ Interactive graphs and charts
- ✅ Play money vs real money tracking
- ✅ Cross-platform support
- ✅ Dashboard with hand history

### Planned Features
- 🔜 On-demand hand advisor
- 🔜 Opponent tracking
- 🔜 Tournament mode
- 🔜 Export reports (PDF/CSV)
- 🔜 Mobile app

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- AI powered by [Ollama](https://ollama.ai/)
- Charts by [Chart.js](https://www.chartjs.org/)
- Inspired by PokerTracker and Hold'em Manager

## 📧 Contact

- GitHub Issues: For bugs and feature requests
- Pull Requests: For contributions

## ⭐ Star This Project

If you find this useful, please star the repository!

---

**Made with ❤️ for poker players who want to improve their game**
