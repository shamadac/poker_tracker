# Sample Hand History Data

This folder contains sample PokerStars hand history files for testing the Poker Analyzer app.

## Files Included

- `HH20250115_Z420909_001.txt` - Real money hands ($0.01/$0.02 stakes)
- `HH20250115_Z420909_002.txt` - Real money hands ($0.01/$0.02 stakes)
- `HH20250115_Z420909_003_PlayMoney.txt` - Play money hands (10/20 stakes)

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

- **Total Hands**: 9 hands
- **Real Money**: 6 hands
- **Play Money**: 3 hands
- **Player**: Z420909
- **Win Rate**: ~67% (6 wins, 3 losses/folds)

## Hand Types Included

The sample data includes various scenarios:
- Premium hands (AA, KK, QQ)
- Suited connectors (9s8s)
- Suited broadway (AhKd, QhJh)
- Flush draws and completions
- Pre-flop aggression
- Post-flop play
- All-in situations
- Fold decisions

This variety helps test all features of the analyzer including:
- VPIP and PFR calculations
- Aggression factor tracking
- Position analysis
- Win rate statistics
- Hand strength evaluation
