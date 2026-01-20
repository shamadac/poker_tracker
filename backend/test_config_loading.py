#!/usr/bin/env python3
"""
Test configuration loading to debug .env.local file loading.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Test loading .env.local directly
env_local_path = Path(__file__).parent / '.env.local'
print(f"Looking for .env.local at: {env_local_path}")
print(f"File exists: {env_local_path.exists()}")

if env_local_path.exists():
    print(f"File size: {env_local_path.stat().st_size} bytes")
    
    # Read the file content
    with open(env_local_path, 'r') as f:
        content = f.read()
    print(f"File content:\n{content}")
    
    # Load the file
    load_dotenv(env_local_path, override=True)
    
    # Check environment variables
    print(f"\nEnvironment variables after loading:")
    print(f"USE_DEV_API_KEYS: {os.getenv('USE_DEV_API_KEYS')}")
    print(f"DEV_GROQ_API_KEY: {os.getenv('DEV_GROQ_API_KEY')}")
    print(f"DEV_GEMINI_API_KEY: {os.getenv('DEV_GEMINI_API_KEY')}")

# Now test the actual config
print("\n" + "="*50)
print("Testing actual config loading:")

from app.core.config import settings
print(f"USE_DEV_API_KEYS: {settings.USE_DEV_API_KEYS}")
print(f"DEV_GROQ_API_KEY: {settings.DEV_GROQ_API_KEY}")
print(f"DEV_GEMINI_API_KEY: {settings.DEV_GEMINI_API_KEY}")
print(f"Groq dev key: {settings.get_dev_api_key('groq')}")
print(f"Gemini dev key: {settings.get_dev_api_key('gemini')}")