# Sample Hand History Data

This folder contains real PokerStars hand history files exported from PokerTracker 4 for testing the Poker Analyzer app.

## Files Included

### Real Money Games
- `HH20260114_Z420909_real.txt` - 4 hands at $0.02/$0.05 CAD (Palamedes IV table)
- `HH20260114_Z420909_perihelion_real.txt` - 1 hand at $0.02/$0.05 CAD (Perihelion II table)

### Play Money Games
- `HH20260112_Z420909_playmoney.txt` - 6 hands at 100/200 (Beljawskya IV table)
- `HH20260112_Z420909_eurykleia_playmoney.txt` - 3 hands at 100/200 (Eurykleia IV table)
- `HH20260112_Z420909_burgundia_playmoney.txt` - 6 hands at 100/200 (Burgundia III table)
- `HH20260111_Z420909_kurhah_playmoney.txt` - 1 hand at 100/200 (Kurhah IV 9-max table)

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

- **Total Hands**: 21 hands
- **Real Money**: 5 hands ($0.02/$0.05 CAD)
- **Play Money**: 16 hands (100/200 stakes)
- **Player**: Z420909
- **Date Range**: January 11-14, 2026
- **Tables**: 6-max and 9-max formats

## Hand Types Included

The sample data includes diverse real gameplay scenarios:

**Real Money:**
- Weak hands (8h2d, 8s2c, 3d6c, 4cTh, Ad3h)
- C-bet on flop with bottom pair
- Pre-flop folds with trash hands
- Position play (SB, BB)
- Multi-way pots
- Fold to aggression
- Bad beat with dominated kicker

**Play Money:**
- Premium hands (AhQh, AhJd, KcQd, KhTc, QcKc, 9s9c)
- Two pair situations
- Straight draws and completions
- All-in confrontations
- Bluff attempts
- Multi-way action
- Big pots and coolers

This real data helps test all features of the analyzer including:
- VPIP and PFR calculations
- Position analysis
- Win rate statistics
- Hand selection evaluation
- Fold discipline tracking
- Aggression factor
- Play money vs real money comparison
