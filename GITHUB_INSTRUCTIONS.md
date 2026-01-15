# For Your Friend - How to Get Started

Hey! Your friend set this up for you. Here's how to use it:

## 📥 Download & Install (5 minutes)

1. **Download this repository**
   - Click the green "Code" button at the top
   - Click "Download ZIP"
   - Save it to your Desktop

2. **Extract the ZIP file**
   - Double-click the downloaded ZIP
   - It will create a folder called `poker-analyzer` (or similar)

3. **Run the installer**
   - Open the `poker-analyzer` folder
   - Find the file called `install_and_run.command`
   - **Double-click it**
   - If Mac says "unidentified developer":
     - Right-click the file
     - Click "Open"
     - Click "Open" again in the popup

4. **Follow the prompts**
   - The installer will check everything
   - It will download Ollama if needed
   - It will install the AI model
   - It will start the app automatically

5. **Your browser opens!**
   - Chrome will open to http://localhost:5000
   - You'll see the Poker Analyzer interface

## 🎮 First Time Use

### Setup PokerStars (One Time Only)
1. Open PokerStars
2. Click the Settings gear icon
3. Go to: **Playing History** → **Hand History**
4. Check the box: "**Save My Hand History**"
5. Click **Apply**

### Analyze Your Game
1. Play some poker on PokerStars (or use existing hands)
2. In the Poker Analyzer web page:
   - Click "**Scan for Hand Histories**"
   - Click "**Analyze Hands & Generate Report**"
3. Wait 2-3 minutes for AI analysis
4. Read your comprehensive report!

## 📊 What You'll See

### Overall Playstyle Report
- Your key statistics (VPIP, PFR, Aggression, Win Rate)
- What you're doing well (Strengths)
- What needs work (Areas for Improvement)
- AI Coach recommendations

### Individual Hand Analysis
- Visual display of your cards with suits (♠ ♥ ♦ ♣)
- Community cards (flop, turn, river)
- Complete betting action
- AI feedback on your decisions
- Click "Show Full Hand History" for complete details

### Comprehensive Evaluation
- Overall assessment of your playstyle
- Top 3 things to improve immediately
- Long-term development plan
- Specific actions to take

## 🔄 Using It Again

Next time you want to analyze:

**Option 1: Quick Start**
- Double-click `install_and_run.command` again
- It will check everything and start the app

**Option 2: If Already Running**
- Just open Chrome
- Go to: http://localhost:5000

## 💡 Tips

- **Start small**: Analyze 5 hands first to see how it works
- **Be patient**: First analysis takes longer (loading AI)
- **Read carefully**: The AI gives specific, actionable advice
- **Use regularly**: Analyze after each session to track improvement
- **Focus**: Pick ONE thing to improve at a time

## 🔧 If Something Goes Wrong

### "Ollama not connected"
- Open Terminal (search for it in Spotlight)
- Type: `ollama serve`
- Press Enter
- Try the app again

### "No hands found"
- Make sure you've played some hands on PokerStars
- Check that hand history is enabled (see setup above)
- The app looks here: `~/Library/Application Support/PokerStars/HandHistory/`

### App won't start
- Open Terminal
- Type: `cd ` (with a space after cd)
- Drag the poker-analyzer folder into Terminal
- Press Enter
- Type: `python3 app.py`
- Press Enter

### Need More Help?
- Read `SETUP_GUIDE.md` for detailed instructions
- Read `README.md` for technical details
- Check that Ollama is installed: Open Terminal, type `ollama list`

## 🔒 Privacy

Everything runs on YOUR Mac:
- No internet required (after setup)
- Your hands never leave your computer
- AI runs completely offline
- 100% private

## 🎯 Getting Better at Poker

1. **Analyze regularly** - After each session
2. **Focus on mistakes** - Read the "Areas for Improvement"
3. **Implement one thing** - Pick one tip and focus on it
4. **Track progress** - Keep notes on what you're working on
5. **Be patient** - Improvement takes time

---

**Questions?** Your friend who set this up can help, or check the other documentation files in this folder.

**Enjoy improving your poker game! 🃏**
