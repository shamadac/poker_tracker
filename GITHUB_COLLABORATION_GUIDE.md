# GitHub Collaboration Guide for Beginners

## 🎯 Goal
You and your friend want to work on the same poker analyzer project together.

## 📚 Key Concepts (Simple Explanation)

### What is Git?
Git tracks changes to your code. Think of it like "Track Changes" in Microsoft Word, but for code.

### What is GitHub?
GitHub is like Google Drive for code. It stores your project online so you and your friend can both access it.

### Key Terms:
- **Repository (Repo)**: The project folder on GitHub
- **Commit**: Saving your changes with a description
- **Push**: Uploading your changes to GitHub
- **Pull**: Downloading changes from GitHub
- **Branch**: A separate version to work on without affecting the main code
- **Merge**: Combining changes from different branches
- **Fork**: Your own copy of someone else's project

## 🚀 Setup Guide

### Step 1: Install Git

**macOS:**
```bash
# Check if you have it
git --version

# If not, install with Homebrew
brew install git

# Or download from: https://git-scm.com/download/mac
```

**Windows:**
```bash
# Download from: https://git-scm.com/download/win
# Run the installer (use default settings)
```

### Step 2: Configure Git (First Time Only)

```bash
# Set your name (will appear on commits)
git config --global user.name "Your Name"

# Set your email (use your GitHub email)
git config --global user.email "your.email@example.com"

# Check your settings
git config --global --list
```

### Step 3: Create a GitHub Account
1. Go to https://github.com
2. Sign up (free)
3. Verify your email

## 🔄 Two Collaboration Approaches

### Option A: Your Friend Adds You as Collaborator (Recommended)

**Your Friend Does:**
1. Go to the GitHub repository
2. Click **Settings** tab
3. Click **Collaborators** (left sidebar)
4. Click **Add people**
5. Enter your GitHub username
6. You'll get an email invitation

**You Do:**
1. Accept the invitation
2. Now you both have full access!

### Option B: Fork the Repository (Alternative)

**You Do:**
1. Go to your friend's GitHub repo
2. Click **Fork** button (top right)
3. Now you have your own copy
4. Make changes in your copy
5. Submit **Pull Requests** to your friend's repo

**We'll use Option A - it's simpler!**

## 📝 Basic Workflow (Daily Use)

### First Time: Clone the Repository

```bash
# Navigate to where you want the project
cd ~/Desktop/Projects

# Clone the repository (get the URL from GitHub)
git clone https://github.com/your-friend/poker-analyzer.git

# Enter the project folder
cd poker-analyzer

# You now have the code!
```

### Daily Workflow: The Golden Rules

#### 1. ALWAYS Pull Before You Start Working
```bash
# Get the latest changes from GitHub
git pull origin main

# This downloads any changes your friend made
```

#### 2. Make Your Changes
- Edit files
- Add features
- Fix bugs
- Test everything

#### 3. Check What You Changed
```bash
# See what files you modified
git status

# See the actual changes
git diff
```

#### 4. Stage Your Changes
```bash
# Add specific files
git add app.py
git add static/graphs.js

# Or add everything
git add .
```

#### 5. Commit Your Changes
```bash
# Commit with a clear message
git commit -m "Added graphs page with 6 interactive charts"

# Good commit messages:
# ✅ "Fixed bug in hand parser for Windows paths"
# ✅ "Added play money vs real money detection"
# ✅ "Updated AI model to llama3.1:8b"
# ❌ "changes"
# ❌ "stuff"
# ❌ "asdf"
```

#### 6. Push to GitHub
```bash
# Upload your changes
git push origin main

# Your friend can now see your changes!
```

## 🔀 Working Together Without Conflicts

### The Problem: Merge Conflicts
If you and your friend edit the same file at the same time, Git doesn't know which version to keep.

### The Solution: Communication + Branches

#### Strategy 1: Communicate (Simple)
- Tell each other what you're working on
- "I'm working on the graphs page"
- "I'm fixing the hand parser"
- Don't edit the same files at the same time

#### Strategy 2: Use Branches (Better)

**Create a Branch for Your Feature:**
```bash
# Create and switch to a new branch
git checkout -b add-hand-advisor

# Now you're on the "add-hand-advisor" branch
# Your friend is still on "main"
```

**Work on Your Branch:**
```bash
# Make changes
# Add files
# Commit

git add .
git commit -m "Added hand advisor feature"
git push origin add-hand-advisor
```

**Merge Your Branch (When Done):**
```bash
# Switch back to main
git checkout main

# Pull latest changes
git pull origin main

# Merge your branch
git merge add-hand-advisor

# Push to GitHub
git push origin main

# Delete the branch (optional)
git branch -d add-hand-advisor
```

## 🆘 Common Scenarios

### Scenario 1: You Both Changed Different Files
```bash
# You changed graphs.js
# Friend changed app.py

git pull origin main
# ✅ No conflict! Git merges automatically

git push origin main
# ✅ Done!
```

### Scenario 2: You Both Changed the Same File
```bash
git pull origin main
# ⚠️ CONFLICT in app.py

# Git marks the conflicts in the file:
<<<<<<< HEAD
Your changes
=======
Friend's changes
>>>>>>> main

# Fix manually:
# 1. Open app.py
# 2. Decide which changes to keep
# 3. Remove the <<<, ===, >>> markers
# 4. Save the file

git add app.py
git commit -m "Resolved merge conflict in app.py"
git push origin main
```

### Scenario 3: You Want to Undo Changes
```bash
# Undo changes to a file (before commit)
git checkout -- app.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1

# Undo a pushed commit (create new commit that undoes it)
git revert HEAD
git push origin main
```

## 📋 Recommended Workflow for You Two

### Setup (One Time):
1. Your friend adds you as collaborator
2. You clone the repository
3. You both configure Git

### Daily Routine:

**Before Starting Work:**
```bash
git pull origin main
```

**While Working:**
```bash
# Make changes
# Test locally
```

**When Done:**
```bash
git status                    # Check what changed
git add .                     # Stage all changes
git commit -m "Description"   # Commit with message
git pull origin main          # Get latest changes
git push origin main          # Upload your changes
```

### Communication:
- Use GitHub Issues for tasks
- Use Pull Requests for big features
- Message each other: "I'm pushing changes to app.py"

## 🎯 Practical Example: Your Current Situation

### What You Need to Do:

#### 1. Initialize Your Local Repository
```bash
cd ~/Desktop/Projects/poker_tracker-main

# Initialize git (if not already)
git init

# Add all your improved files
git add .

# Commit everything
git commit -m "Major improvements: graphs page, Windows support, llama3.1 model, play money detection"
```

#### 2. Connect to Your Friend's GitHub Repo
```bash
# Add the remote repository (get URL from your friend)
git remote add origin https://github.com/your-friend/poker-analyzer.git

# Check it's added
git remote -v
```

#### 3. Push Your Changes
```bash
# Push to GitHub
git push -u origin main

# If your friend's repo has different history:
git pull origin main --allow-unrelated-histories
git push origin main
```

## 🔧 Useful Git Commands

### Check Status
```bash
git status              # What files changed?
git log                 # History of commits
git log --oneline       # Compact history
git diff                # What changed in files?
git branch              # List branches
```

### Undo Things
```bash
git checkout -- file.py     # Undo changes to file
git reset HEAD file.py      # Unstage file
git clean -fd               # Remove untracked files
```

### Branches
```bash
git branch feature-name         # Create branch
git checkout feature-name       # Switch to branch
git checkout -b feature-name    # Create and switch
git branch -d feature-name      # Delete branch
git merge feature-name          # Merge branch into current
```

### Remote
```bash
git remote -v                   # Show remotes
git fetch origin                # Download changes (don't merge)
git pull origin main            # Download and merge
git push origin main            # Upload changes
```

## 📱 GitHub Desktop (Easier Alternative)

If command line is intimidating, use **GitHub Desktop**:
- Download: https://desktop.github.com
- Visual interface
- Drag and drop
- Click buttons instead of typing commands
- Perfect for beginners!

## 🎓 Learning Resources

### Quick References:
- GitHub Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf
- Interactive Tutorial: https://learngitbranching.js.org

### Videos:
- "Git and GitHub for Beginners" on YouTube
- GitHub's own tutorials: https://skills.github.com

## ⚠️ Important Tips

### DO:
- ✅ Pull before you start working
- ✅ Commit often with clear messages
- ✅ Push at the end of your work session
- ✅ Communicate with your friend
- ✅ Test before pushing

### DON'T:
- ❌ Work on the same file simultaneously
- ❌ Commit broken code
- ❌ Use vague commit messages
- ❌ Force push (git push -f) unless you know what you're doing
- ❌ Commit sensitive data (passwords, API keys)

## 🚀 Next Steps for You

1. **Install Git** (if not already)
2. **Configure Git** with your name and email
3. **Create GitHub account**
4. **Ask your friend to add you as collaborator**
5. **Clone the repository**
6. **Push your improvements**
7. **Start collaborating!**

## 💬 Quick Command Reference Card

```bash
# Daily workflow
git pull origin main          # Start: Get latest
# ... make changes ...
git add .                     # Stage changes
git commit -m "message"       # Save changes
git push origin main          # Upload changes

# Check things
git status                    # What changed?
git log --oneline            # History

# Branches
git checkout -b feature      # New branch
git checkout main            # Back to main
git merge feature            # Merge branch

# Undo
git checkout -- file         # Undo file changes
git reset --soft HEAD~1      # Undo last commit
```

## 🎉 You're Ready!

Git seems complex at first, but you'll use these same 5-10 commands 90% of the time:
- `git pull`
- `git add`
- `git commit`
- `git push`
- `git status`

Start with these, and you'll be collaborating like a pro in no time!

---

**Need Help?**
- GitHub has great documentation
- Your friend can help
- Google "git [what you want to do]"
- Stack Overflow has answers to everything

**Remember**: Everyone makes mistakes with Git. It's okay! Almost everything can be undone.
