# Using Gemini AI (Pre-configured)

Good news! This project comes with a pre-configured Google Gemini API key, so you can start analyzing hands immediately without any setup.

## Quick Start

1. **Clone the repository**
```bash
git clone <repo-url>
cd poker-analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start the app**
```bash
python app.py
```

4. **Open in browser**
Go to: `http://localhost:5000`

5. **Select Gemini**
- The Gemini API key is already configured
- Just select "Google Gemini (Cloud)" option
- Click "Save Settings"
- Start analyzing!

## Why Gemini?

- **Fast**: Cloud-based analysis is quick
- **Free Tier**: Generous free quota for personal use
- **No Installation**: No need to install Ollama or download large models
- **Works Everywhere**: Windows, Mac, Linux - just needs internet

## Model Options

- **Gemini 1.5 Flash** (Recommended): Fastest, best for free tier
- **Gemini Pro**: More detailed analysis, uses more quota

## Free Tier Limits

Google's free tier includes:
- 15 requests per minute
- 1,500 requests per day
- 1 million requests per month

This is more than enough for analyzing poker hands!

## Optional: Use Your Own API Key

If you want to use your own API key:

1. Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. In the web interface, paste your key in the "Gemini API Key" field
3. Click "Save Settings"

## Switching to Ollama

If you prefer local analysis:

1. Select "Ollama (Local)" in the web interface
2. Click "Setup Ollama" if not installed
3. The app will guide you through installation

## Troubleshooting

**"Gemini API error"**
- Check your internet connection
- The free tier key might have hit rate limits (wait a minute)

**Want more quota?**
- Use your own API key (still free)
- Or switch to Ollama for unlimited local analysis
