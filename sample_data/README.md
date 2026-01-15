# Sample Hand History Data

This folder contains real PokerStars hand history files exported from PokerTracker 4 for testing the Poker Analyzer app.

## Files Included

- `HH20260114_Z420909_real.txt` - Real money hands ($0.02/$0.05 CAD stakes)

## How to Use

### Option 1: Copy to hand_histories folder
```bash
cp sample_data/*.txt hand_histories/
```

### Option 2: Update config.json
Change the `hand_history_dir` setting to point to `sample_data`:
```json
{
  "hand_history_dir": "sample_data"
}
```

### Option 3: Test with your own data
Replace these sample files with your actual PokerStars hand history files. The app will automatically detect and parse them.

## Sample Data Statistics

- **Total Hands**: 4 hands
- **Stakes**: $0.02/$0.05 CAD
- **Player**: Z420909
- **Table**: Palamedes IV (6-max)
- **Date**: January 14, 2026

## Hand Types Included

The sample data includes real gameplay scenarios:
- Weak hands (8h2d, 8s2c, 3d6c, 4cTh)
- C-bet on flop with bottom pair
- Pre-flop folds with trash hands
- Position play (SB, BB)
- Multi-way pots
- Fold to aggression

This real data helps test all features of the analyzer including:
- VPIP and PFR calculations
- Position analysis
- Win rate statistics
- Hand selection evaluation
- Fold discipline tracking
