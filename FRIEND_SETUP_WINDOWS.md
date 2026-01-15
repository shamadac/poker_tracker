# 🚀 Setup Guide for Your Friend (Windows)

## 🎯 Best Approach: Clone Fresh

**DO THIS:** Clone the repository (get a fresh copy from GitHub)
**DON'T:** Try to use the old project folder

**Why?**
- ✅ Gets all the new improvements automatically
- ✅ Properly connected to GitHub
- ✅ No conflicts with old files
- ✅ Clean start

---

## 📋 Step-by-Step Instructions

### Step 1: Install Git (If Not Already)

1. Download Git for Windows: https://git-scm.com/download/win
2. Run the installer
3. Use default settings (just click "Next")
4. Finish installation

**Verify it worked:**
Open Command Prompt and type:
```bash
git --version
```
Should show: `git version 2.x.x`

### Step 2: Configure Git

Open Command Prompt and run:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Replace with your actual name and email.

### Step 3: Choose a Location

Decide where to put the project. Good options:
- `C:\Users\YourName\Documents\Projects\`
- `C:\Users\YourName\Desktop\`
- `C:\Projects\`

### Step 4: Clone the Repository

Open Command Prompt and navigate to your chosen location:

```bash
# Example: Go to Documents
cd C:\Users\YourName\Documents

# Create a Projects folder (if it doesn't exist)
mkdir Projects
cd Projects

# Clone the repository
git clone https://github.com/shamadac/poker_tracker.git

# Enter the folder
cd poker_tracker
```

**What this does:**
- Downloads all files from GitHub
- Creates a `poker_tracker` folder
- Sets up Git automatically
- Gets all of Zhilong's improvements!

### Step 5: Open in Kiro

1. Open Kiro
2. File → Open Folder
3. Navigate to: `C:\Users\YourName\Documents\Projects\poker_tracker`
4. Click "Select Folder"

Done! You now have the improved version!

---

## 🎮 What About the Old Folder?

### Option 1: Keep It (Recommended)
- Rename it to `poker_tracker_old`
- Keep as backup
- Don't use it for development

### Option 2: Delete It
- Only if you don't need the old version
- Make sure you have no important changes there

### Option 3: Archive It
- Zip it up
- Store somewhere safe
- Delete the folder

---

## 🔧 Setting Up the App (Windows)

After cloning, set up the app:

### Quick Setup:
```bash
# In the poker_tracker folder
install_windows.bat
```

This will:
- Check Python
- Install Ollama
- Download AI model
- Install dependencies

### Or Manual Setup:

1. **Install Python** (if not already):
   - Download from: https://www.python.org/downloads/
   - Check "Add Python to PATH"

2. **Install Ollama**:
   - Download from: https://ollama.ai/download
   - Install and run

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download AI Model**:
   ```bash
   ollama pull llama3.1:8b
   ```

5. **Start the App**:
   ```bash
   python app.py
   ```

6. **Open Browser**:
   - Go to: http://localhost:5001

---

## 🔄 Daily Workflow (After Setup)

### Before You Start Working:
```bash
git pull origin main
```
Gets Zhilong's latest changes.

### After Making Changes:
```bash
git add .
git commit -m "What you changed"
git push origin main
```
Uploads your changes.

---

## 🎯 What You'll Get

After cloning, you'll have:
- ✅ Interactive graphs page (6 charts)
- ✅ Windows support (install_windows.bat)
- ✅ Llama 3.1 8B model (better AI)
- ✅ Beginner-friendly analysis
- ✅ Play money vs real money detection
- ✅ Dashboard improvements
- ✅ Complete documentation

---

## 🆘 Troubleshooting

### "git is not recognized"
- Restart Command Prompt after installing Git
- Or restart computer

### "Permission denied"
- Make sure you're added as collaborator
- Check your GitHub account

### "Port 5001 already in use"
- Edit `app.py`
- Change port to 5002 or 5003

### "Ollama not found"
- Install from: https://ollama.ai/download
- Make sure it's running

---

## 📱 Alternative: GitHub Desktop (Easier)

If command line is confusing:

1. **Download GitHub Desktop**: https://desktop.github.com
2. **Install it**
3. **Sign in** with your GitHub account
4. **Clone Repository**:
   - File → Clone Repository
   - Select: `shamadac/poker_tracker`
   - Choose location
   - Click "Clone"
5. **Open in Kiro**:
   - Right-click repository
   - "Open in Visual Studio Code" (or Kiro)

**Benefits:**
- Visual interface
- No commands to remember
- Easy to see changes
- Perfect for beginners

---

## 🤝 Working Together

### Communication is Key:
- Tell Zhilong what you're working on
- "I'm editing the graphs page today"
- Avoid editing the same files

### Pull Often:
- Run `git pull` every morning
- Before you start working
- Gets latest changes

### Push Often:
- Don't wait days to push
- Push at end of each work session
- Keeps everyone in sync

### Use Branches (Optional):
- For big features
- Keeps main stable
- See `BRANCHES_EXPLAINED.md`

---

## 📊 Comparing Approaches

### Clone Fresh (Recommended) ✅
**Pros:**
- Clean start
- All improvements included
- Properly connected to GitHub
- No conflicts

**Cons:**
- Need to set up app again
- Lose any local changes (if any)

### Use Old Folder ❌
**Pros:**
- Already set up
- Keep local changes

**Cons:**
- Missing all improvements
- Not connected to GitHub
- Need to manually update files
- Potential conflicts
- Messy

---

## 🎯 Recommended Steps

1. **Rename old folder** to `poker_tracker_old`
2. **Clone fresh** from GitHub
3. **Set up the app** (run install_windows.bat)
4. **Open in Kiro**
5. **Start collaborating!**

---

## 📚 Resources

After cloning, read these files:
- `SUCCESS.md` - Daily workflow
- `BRANCHES_EXPLAINED.md` - Understanding branches
- `GITHUB_COLLABORATION_GUIDE.md` - Complete guide
- `WINDOWS_SETUP.md` - Windows-specific help

---

## ✅ Quick Checklist

- [ ] Install Git
- [ ] Configure Git (name and email)
- [ ] Clone repository
- [ ] Open in Kiro
- [ ] Run install_windows.bat
- [ ] Test the app (http://localhost:5001)
- [ ] Make a test change
- [ ] Commit and push
- [ ] Check GitHub to see your change

---

## 🎉 You're Ready!

After cloning, you'll have the latest version with all improvements. You and Zhilong can now work together seamlessly!

**Questions?** Check the other guides in the repository or ask Zhilong.

---

**Summary:** Clone fresh, don't use the old folder. It's cleaner and better! 🚀
