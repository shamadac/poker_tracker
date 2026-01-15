# On-Demand Hand Advisor Feature - Implementation Plan

## 🎯 Feature Overview

A real-time poker decision helper that gives instant advice based on:
1. Your personal playing style (from analyzed hands)
2. Current hand situation
3. Pot odds and game theory

## 📋 User Flow

### Step 1: Access the Advisor
- New page: `/advisor` or modal on main page
- Button: "🎴 Get Hand Advice"

### Step 2: Input Current Situation
User provides:
- **Your Cards**: Select 2 cards (e.g., A♥ 6♣)
- **Position**: Button, Small Blind, Big Blind, Early, Middle, Late
- **Game Stage**: Pre-flop, Flop, Turn, River
- **Community Cards**: (if post-flop)
- **Pot Size**: Current pot amount
- **Bet to Call**: Amount you need to call
- **Your Stack**: Your remaining chips
- **Number of Players**: Still in the hand
- **Opponent Behavior**: Tight/Loose, Aggressive/Passive (optional)

### Step 3: Get Instant Advice
AI analyzes and provides:
- **Recommended Action**: Fold / Call / Raise (with amount)
- **Reasoning**: Why this is the best play
- **Pot Odds**: Calculation and explanation
- **Personalized Note**: Based on your tendencies
  - "You tend to play too loose in this position - be careful"
  - "This is a good spot for you based on your stats"
- **Alternative Plays**: Other options and when to use them
- **Learning Point**: Concept explanation for beginners

## 🎨 UI Design

### Card Selector
```
┌─────────────────────────────────────┐
│  Your Hand                          │
│  ┌───┐ ┌───┐                       │
│  │ A │ │ 6 │  [Change Cards]       │
│  │ ♥ │ │ ♣ │                       │
│  └───┘ └───┘                       │
└─────────────────────────────────────┘
```

### Situation Input (Simple Form)
```
Position: [Dropdown: Button/SB/BB/Early/Middle/Late]
Stage: [Tabs: Pre-Flop | Flop | Turn | River]

Community Cards (if post-flop):
[Card Selector] [Card Selector] [Card Selector] [Card Selector] [Card Selector]

Pot Size: [$____]
To Call: [$____]
Your Stack: [$____]
Players in Hand: [2-9]

[Get Advice Button]
```

### Advice Display
```
┌─────────────────────────────────────┐
│  💡 RECOMMENDED ACTION              │
│                                     │
│  🎯 RAISE to $15                    │
│                                     │
│  WHY:                               │
│  • You have a strong hand (A-high) │
│  • You're in late position         │
│  • Pot odds favor aggression       │
│  • Based on your stats, you don't  │
│    raise enough in this spot       │
│                                     │
│  📊 POT ODDS:                       │
│  You need to win 25% of the time   │
│  Your hand wins ~40% (estimated)   │
│  ✅ Good call!                      │
│                                     │
│  🎓 LEARNING POINT:                 │
│  Position is power in poker. When  │
│  you're on the button, you act     │
│  last and have more information.   │
│                                     │
│  ⚠️ PERSONAL NOTE:                  │
│  Your stats show you fold too      │
│  often with Ace-high. This is a    │
│  profitable spot to be aggressive. │
└─────────────────────────────────────┘
```

## 🔧 Technical Implementation

### Frontend (advisor.html)
- Card selector component (visual cards)
- Form with all inputs
- Real-time validation
- Loading state during AI analysis
- Beautiful advice display

### Backend (app.py)
```python
@app.route('/api/advisor/analyze', methods=['POST'])
def analyze_hand_advisor():
    """
    Get instant advice for a specific hand situation.
    """
    data = request.json
    
    # Get user's playstyle profile
    all_hands = app.config.get('cached_hands', [])
    playstyle = playstyle_analyzer.analyze_playstyle(all_hands)
    
    # Get AI advice
    advice = analyzer.get_hand_advice(
        cards=data['cards'],
        position=data['position'],
        stage=data['stage'],
        community_cards=data.get('community_cards'),
        pot_size=data['pot_size'],
        to_call=data['to_call'],
        stack=data['stack'],
        players=data['players'],
        playstyle=playstyle
    )
    
    return jsonify({
        'success': True,
        'advice': advice
    })
```

### AI Prompt (ollama_analyzer.py)
```python
def get_hand_advice(self, cards, position, stage, community_cards, 
                    pot_size, to_call, stack, players, playstyle):
    """
    Generate instant advice for a specific hand situation.
    """
    prompt = f"""You are a poker coach giving INSTANT advice to a BEGINNER player.

PLAYER'S HAND: {cards}
POSITION: {position}
STAGE: {stage}
COMMUNITY CARDS: {community_cards or 'None (pre-flop)'}
POT SIZE: ${pot_size}
TO CALL: ${to_call}
YOUR STACK: ${stack}
PLAYERS IN HAND: {players}

PLAYER'S TENDENCIES (from their history):
- VPIP: {playstyle.get('vpip')}%
- PFR: {playstyle.get('pfr')}%
- Aggression: {playstyle.get('aggression')}
- Common mistakes: {playstyle.get('common_mistakes')}

Provide advice in this EXACT format:

## RECOMMENDED ACTION
[FOLD / CALL / RAISE to $X]

## WHY THIS IS THE RIGHT PLAY
[3-4 bullet points explaining the reasoning]

## POT ODDS CALCULATION
[Simple explanation: "You need to win X% of the time. Your hand wins ~Y%. This makes it a [good/bad] call."]

## PERSONALIZED NOTE
[Based on their tendencies, what should they watch out for? Be specific and helpful.]

## LEARNING POINT
[Explain one poker concept they should understand from this situation]

Keep it simple, clear, and actionable. This player is a BEGINNER."""
    
    # Call Ollama API
    # ... (similar to existing analyze_hand method)
```

## 🎯 Key Features

### 1. Personalization
- Uses player's actual stats
- Identifies their specific weaknesses
- Tailored advice based on their tendencies

### 2. Educational
- Explains pot odds simply
- Teaches concepts
- Shows why, not just what

### 3. Fast
- Instant response (2-3 seconds)
- No need to wait for full analysis
- Can use during actual play

### 4. Beginner-Friendly
- Simple language
- Visual card selector
- Clear recommendations
- No jargon

## 📱 Mobile-Friendly
- Large touch targets for card selection
- Simple form layout
- Easy to use on phone during play

## 🚀 Future Enhancements

### Phase 2:
- Save favorite hands
- History of advice requests
- Compare advice to what you actually did
- Track improvement over time

### Phase 3:
- Opponent modeling (track specific opponents)
- Range analysis
- GTO (Game Theory Optimal) comparison
- Tournament vs cash game modes

### Phase 4:
- Real-time integration (browser extension?)
- Voice input
- Quick shortcuts for common situations

## 💡 Usage Scenarios

### Scenario 1: During Live Play
"I'm playing online right now. I have A♥6♣ on the button. Should I raise?"
→ Quick input → Instant advice

### Scenario 2: Hand Review
"I folded this hand yesterday. Was that right?"
→ Input the situation → See if you made the right call

### Scenario 3: Learning
"I want to understand when to play Ace-rag hands"
→ Try different scenarios → Learn the patterns

## 🎓 Educational Value

This feature turns the app from a **passive analyzer** into an **active coach**:
- Learn by doing
- Get feedback immediately
- Understand your specific leaks
- Practice decision-making

## 📊 Success Metrics

- How often users get advice
- Accuracy of advice (compare to GTO solvers)
- User satisfaction
- Improvement in actual play (tracked through hand history)

## 🔐 Privacy

- All analysis happens locally
- No hand data sent to external servers
- Your poker decisions stay private

## Next Steps

1. ✅ Create UI mockup
2. ✅ Design card selector component
3. ✅ Build form with validation
4. ✅ Implement backend endpoint
5. ✅ Create AI prompt for advice
6. ✅ Add pot odds calculator
7. ✅ Test with real scenarios
8. ✅ Polish UI/UX
9. ✅ Add to navigation

Ready to implement!
