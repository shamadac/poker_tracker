# Play Money vs Real Money Detection

## ✅ Feature Implemented

The app now distinguishes between play money and real money games!

### What Was Added:

1. **Automatic Detection**
   - Parser identifies play money games by looking for "(Play Money)" in hand history
   - Real money games are identified by $ signs in stakes
   - Each hand is tagged with `is_play_money` flag

2. **Dashboard Filter**
   - New dropdown filter: "All Games", "Real Money Only", "Play Money Only"
   - Instantly filter the hand history table by money type
   - Works in combination with other filters (search, result type)

3. **Visual Badges**
   - Each hand in the table shows a colored badge:
     - **Play Money**: Purple gradient badge
     - **Real Money**: Pink/red gradient badge
   - Easy to see at a glance which games are which

4. **Statistics Breakdown**
   - Dashboard header shows: "● 45 Play Money | ● 5 Real Money"
   - Backend calculates separate statistics for each type
   - Can be extended to show separate stats panels in future

5. **New Table Column**
   - Added "Type" column between "Date" and "Game"
   - Shows the money type badge for each hand
   - Sortable and filterable

### How to Use:

1. **View Dashboard** (http://localhost:5001/dashboard)
2. **See the breakdown** in the header (e.g., "45 Play Money | 5 Real Money")
3. **Use the filter** dropdown to show only:
   - All Games (default)
   - Real Money Only
   - Play Money Only
4. **Look at badges** in the "Type" column to quickly identify each hand

### Technical Details:

**Modified Files:**
- `hand_parser.py`: Added `_is_play_money()` method and `is_play_money` field
- `app.py`: Updated dashboard API to separate and count play/real money hands
- `templates/dashboard.html`: Added money type filter and table column
- `static/dashboard.js`: Added filter logic and badge rendering
- `static/dashboard.css`: Added styling for money type badges

**Detection Logic:**
```python
def _is_play_money(self, text: str) -> bool:
    """Determine if this is a play money game."""
    return '(Play Money)' in text
```

### Current Stats (Your Data):
- **Total Hands**: 50
- **Play Money**: 45 hands
- **Real Money**: 5 hands

This helps you:
- Focus analysis on real money games (where it matters most)
- Compare your play style between play money and real money
- Track progress as you transition from play money to real money
- Separate practice hands from serious games

### Future Enhancements (Optional):
- Separate statistics panels for play money vs real money
- Win rate comparison between the two types
- Recommendations specific to real money play
- Filter the main analysis page by money type
