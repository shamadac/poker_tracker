#!/usr/bin/env python3
"""
Development mode toggle script.

This script allows you to easily switch between development and production modes
for API key usage.
"""

import os
import sys
from pathlib import Path

def enable_dev_mode():
    """Enable development mode - use your API keys as fallbacks."""
    env_path = Path(__file__).parent / '.env'
    
    # Read current .env file
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add USE_DEV_API_KEYS
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('USE_DEV_API_KEYS='):
            lines[i] = 'USE_DEV_API_KEYS=true\n'
            updated = True
            break
    
    if not updated:
        lines.append('USE_DEV_API_KEYS=true\n')
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("✅ Development mode ENABLED")
    print("   - Your API keys will be used as fallbacks")
    print("   - Users can still provide their own keys")
    print("   - Perfect for local development and testing")

def disable_dev_mode():
    """Disable development mode - require users to provide their own API keys."""
    env_path = Path(__file__).parent / '.env'
    
    # Read current .env file
    lines = []
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    
    # Update or add USE_DEV_API_KEYS
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('USE_DEV_API_KEYS='):
            lines[i] = 'USE_DEV_API_KEYS=false\n'
            updated = True
            break
    
    if not updated:
        lines.append('USE_DEV_API_KEYS=false\n')
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("🔒 Development mode DISABLED")
    print("   - Users must provide their own API keys")
    print("   - No fallback to development keys")
    print("   - Ready for production deployment")

def check_status():
    """Check current development mode status."""
    env_path = Path(__file__).parent / '.env'
    
    use_dev_keys = False
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('USE_DEV_API_KEYS='):
                    use_dev_keys = line.strip().split('=')[1].lower() == 'true'
                    break
    
    if use_dev_keys:
        print("🔧 Development mode is ENABLED")
        print("   - Your API keys are available as fallbacks")
        print("   - Great for local development and testing")
    else:
        print("🔒 Development mode is DISABLED")
        print("   - Users must provide their own API keys")
        print("   - Production-ready configuration")
    
    return use_dev_keys

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("API Key Development Mode Toggle")
        print("=" * 40)
        print()
        check_status()
        print()
        print("Usage:")
        print("  python dev_mode.py enable   - Enable development mode")
        print("  python dev_mode.py disable  - Disable development mode")
        print("  python dev_mode.py status   - Check current status")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'enable':
        enable_dev_mode()
    elif command == 'disable':
        disable_dev_mode()
    elif command == 'status':
        check_status()
    else:
        print(f"Unknown command: {command}")
        print("Use: enable, disable, or status")

if __name__ == "__main__":
    main()