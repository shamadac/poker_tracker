#!/usr/bin/env python3
"""
Script to import all hand history data provided by user.
Run this to add all ~70 hands to the hand_histories folder.
"""

# This script would parse the complete hand history from the user's message
# and save it to properly formatted files.

# Due to the large amount of data, the user should:
# 1. Export complete hand history from PokerTracker 4 as .txt file
# 2. Place it in hand_histories/ folder
# 3. The app will auto-detect all hands

print("To add all your hands:")
print("1. In PokerTracker 4, select all hands you want to analyze")
print("2. Right-click > Export Hand History")
print("3. Save the .txt file to the hand_histories/ folder")
print("4. The app will automatically detect all hands")
print("\nCurrent hand count in files:")

import os
import glob

hand_files = glob.glob("hand_histories/*.txt")
total_hands = 0

for file in hand_files:
    with open(file, 'r') as f:
        content = f.read()
        hands = content.count("PokerStars Hand #")
        total_hands += hands
        print(f"  {os.path.basename(file)}: {hands} hands")

print(f"\nTotal: {total_hands} hands detected")
