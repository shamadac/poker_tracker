# 🔧 Virtual Environment Setup Guide

## 🎯 What is a Virtual Environment?

A virtual environment is an isolated Python environment for your project. Think of it like a separate container that keeps all your project's dependencies separate from other Python projects.

### Why Use It?
- ✅ **Isolation**: Dependencies don't conflict with other projects
- ✅ **Reproducibility**: Same versions for everyone
- ✅ **Clean**: Easy to delete and recreate
- ✅ **Professional**: Industry standard practice

---

## 🚀 Quick Setup

### macOS/Linux:
```bash
./setup_venv.sh
./start_venv.sh
```

### Windows:
```bash
setup_venv.bat
start_venv.bat
```

That's it! The scripts handle everything.

---

## 📋 Manual Setup (If You Want to Understand)

### Step 1: Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv .venv
```

**Windows:**
```bash
python -m venv .venv
```

This creates a `.venv` folder with an isolated Python environment.

### Step 2: Activate Virtual Environment

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate.bat
```

You'll see `(.venv)` in your terminal prompt.

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Run the App

```bash
python app.py
```

### Step 5: Deactivate (When Done)

```bash
deactivate
```

---

## 📦 What's Installed?

The virtual environment includes:

```
Flask==3.1.2              # Web framework
flask-cors==6.0.2         # Cross-origin support
requests==2.32.5          # HTTP library
blinker==1.9.0            # Signals
certifi==2026.1.4         # SSL certificates
charset-normalizer==3.4.4 # Character encoding
click==8.3.1              # CLI utilities
idna==3.11                # Domain names
itsdangerous==2.2.0       # Security
Jinja2==3.1.6             # Templates
MarkupSafe==3.0.3         # String escaping
urllib3==2.6.3            # HTTP client
Werkzeug==3.1.5           # WSGI utilities
```

---

## 🔄 Daily Workflow

### Starting Work:

**macOS/Linux:**
```bash
source .venv/bin/activate
python app.py
```

**Windows:**
```bash
.venv\Scripts\activate.bat
python app.py
```

**Or use the start scripts:**
```bash
./start_venv.sh          # macOS/Linux
start_venv.bat           # Windows
```

### Stopping:
- Press `Ctrl+C` to stop the server
- Type `deactivate` to exit virtual environment

---

## 🆘 Troubleshooting

### Problem: "No module named 'flask'"

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate.bat # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Problem: ".venv folder doesn't exist"

**Solution:**
```bash
# Run setup script
./setup_venv.sh          # macOS/Linux
setup_venv.bat           # Windows
```

### Problem: "Permission denied" (macOS/Linux)

**Solution:**
```bash
chmod +x setup_venv.sh
chmod +x start_venv.sh
```

### Problem: Virtual environment not activating (Windows)

**Solution:**
```bash
# Run PowerShell as Administrator
Set-ExecutionPolicy RemoteSigned

# Then try again
.venv\Scripts\activate.bat
```

### Problem: Wrong Python version

**Solution:**
```bash
# Delete virtual environment
rm -rf .venv  # macOS/Linux
rmdir /s .venv  # Windows

# Create with specific Python version
python3.11 -m venv .venv  # macOS/Linux
py -3.11 -m venv .venv    # Windows
```

---

## 🔍 Checking Your Setup

### Verify Virtual Environment is Active:

**macOS/Linux:**
```bash
which python
# Should show: /path/to/project/.venv/bin/python
```

**Windows:**
```bash
where python
# Should show: C:\path\to\project\.venv\Scripts\python.exe
```

### Check Installed Packages:

```bash
pip list
```

Should show all the packages from requirements.txt.

### Check Python Version:

```bash
python --version
```

Should be Python 3.8 or higher.

---

## 📁 Project Structure

```
poker_tracker/
├── .venv/                  # Virtual environment (not in Git)
│   ├── bin/               # Executables (macOS/Linux)
│   ├── Scripts/           # Executables (Windows)
│   ├── lib/               # Installed packages
│   └── ...
├── app.py
├── requirements.txt       # Dependencies list
├── requirements_frozen.txt # Exact versions
├── setup_venv.sh          # Setup script (macOS/Linux)
├── setup_venv.bat         # Setup script (Windows)
├── start_venv.sh          # Start script (macOS/Linux)
├── start_venv.bat         # Start script (Windows)
└── ...
```

---

## 🤝 For Collaborators

### When Cloning the Repository:

1. **Clone:**
   ```bash
   git clone https://github.com/shamadac/poker_tracker.git
   cd poker_tracker
   ```

2. **Setup Virtual Environment:**
   ```bash
   ./setup_venv.sh          # macOS/Linux
   setup_venv.bat           # Windows
   ```

3. **Start App:**
   ```bash
   ./start_venv.sh          # macOS/Linux
   start_venv.bat           # Windows
   ```

### When Pulling Updates:

```bash
git pull origin main

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate.bat # Windows

# Update dependencies (if requirements.txt changed)
pip install -r requirements.txt
```

---

## 📝 Adding New Dependencies

### If You Install a New Package:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install the package
pip install package-name

# Update requirements.txt
pip freeze > requirements_frozen.txt

# Or manually add to requirements.txt
echo "package-name>=1.0.0" >> requirements.txt

# Commit the change
git add requirements.txt
git commit -m "Added package-name dependency"
git push origin main
```

### Your Friend Then:

```bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🎯 Best Practices

### DO:
- ✅ Always activate virtual environment before working
- ✅ Use `pip install` inside virtual environment
- ✅ Update requirements.txt when adding packages
- ✅ Commit requirements.txt to Git
- ✅ Use setup scripts for consistency

### DON'T:
- ❌ Install packages globally (outside virtual environment)
- ❌ Commit .venv folder to Git (it's in .gitignore)
- ❌ Mix virtual environments between projects
- ❌ Forget to activate before running app
- ❌ Delete .venv without backing up if you made changes

---

## 🔄 Recreating Virtual Environment

If something goes wrong, you can always recreate:

```bash
# Delete old virtual environment
rm -rf .venv  # macOS/Linux
rmdir /s .venv  # Windows

# Create fresh one
./setup_venv.sh          # macOS/Linux
setup_venv.bat           # Windows
```

All your code is safe - only the virtual environment is deleted.

---

## 📊 Comparison: With vs Without Virtual Environment

### Without Virtual Environment:
```
❌ Packages installed globally
❌ Conflicts with other projects
❌ Hard to reproduce setup
❌ Messy system Python
```

### With Virtual Environment:
```
✅ Isolated dependencies
✅ No conflicts
✅ Easy to reproduce
✅ Clean system Python
✅ Professional setup
```

---

## 🎓 Understanding the Files

### requirements.txt
- Lists dependencies with minimum versions
- Example: `flask>=3.0.0`
- Flexible, allows updates

### requirements_frozen.txt
- Lists exact versions
- Example: `Flask==3.1.2`
- Reproducible, same versions always

### .venv/
- Contains isolated Python environment
- Not committed to Git
- Can be deleted and recreated

### setup_venv.sh / setup_venv.bat
- Creates virtual environment
- Installs dependencies
- Checks Ollama

### start_venv.sh / start_venv.bat
- Activates virtual environment
- Starts the app
- Convenient shortcut

---

## ✅ Quick Checklist

- [ ] Virtual environment created (`.venv` folder exists)
- [ ] Dependencies installed (`pip list` shows packages)
- [ ] Can activate virtual environment
- [ ] App runs successfully
- [ ] `.venv` is in `.gitignore`
- [ ] `requirements.txt` is committed to Git

---

## 🎉 You're Set Up!

Your virtual environment is ready. Use the start scripts for convenience:

```bash
./start_venv.sh          # macOS/Linux
start_venv.bat           # Windows
```

Happy coding! 🚀
