"""
Education content seeder for poker statistics encyclopedia.
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.education import EducationContent, DifficultyLevel, ContentCategory
from ..schemas.education import EducationContentCreate


class EducationContentSeeder:
    """Seed the database with comprehensive poker education content."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_all_content(self) -> None:
        """Seed all education content categories."""
        await self.seed_basic_content()
        await self.seed_advanced_content()
        await self.seed_tournament_content()
        await self.seed_cash_game_content()

    async def seed_basic_content(self) -> None:
        """Seed basic poker statistics content."""
        basic_content = [
            {
                "title": "VPIP (Voluntarily Put Money In Pot)",
                "slug": "vpip-voluntarily-put-money-in-pot",
                "category": ContentCategory.BASIC,
                "difficulty": DifficultyLevel.BEGINNER,
                "definition": "The percentage of hands where a player voluntarily puts money into the pot preflop.",
                "explanation": """VPIP is one of the most fundamental poker statistics. It measures how often a player chooses to play hands by calling, betting, or raising preflop. This excludes forced bets like blinds.

A typical VPIP range:
- Tight players: 15-25%
- Loose players: 30-40%+
- Professional players: Usually 20-30%

VPIP helps you understand a player's preflop hand selection and overall playing style. Tight players have low VPIP, while loose players have high VPIP.""",
                "examples": [
                    "If you play 20 hands out of 100, your VPIP is 20%",
                    "Folding in the big blind to a raise doesn't count toward VPIP",
                    "Calling, betting, or raising preflop all count toward VPIP"
                ],
                "related_stats": ["PFR", "Aggression Factor", "Position Stats"],
                "tags": ["preflop", "fundamental", "hand-selection"],
                "prerequisites": [],
                "learning_objectives": [
                    "Understand what VPIP measures",
                    "Know typical VPIP ranges for different player types",
                    "Use VPIP to categorize opponents"
                ]
            },
            {
                "title": "PFR (Preflop Raise)",
                "slug": "pfr-preflop-raise",
                "category": ContentCategory.BASIC,
                "difficulty": DifficultyLevel.BEGINNER,
                "definition": "The percentage of hands where a player raises preflop.",
                "explanation": """PFR measures how often a player raises when they enter a pot preflop. This is a subset of VPIP - you can't have a higher PFR than VPIP.

The gap between VPIP and PFR tells you about a player's aggression:
- Small gap (VPIP 22%, PFR 18%): Aggressive player who usually raises
- Large gap (VPIP 35%, PFR 8%): Passive player who calls a lot

Typical PFR ranges:
- Tight-aggressive: 15-20%
- Loose-aggressive: 20-25%
- Passive players: 5-12%""",
                "examples": [
                    "VPIP 25%, PFR 20% = Aggressive player",
                    "VPIP 30%, PFR 8% = Passive calling station",
                    "PFR can never be higher than VPIP"
                ],
                "related_stats": ["VPIP", "Aggression Factor", "3-Bet %"],
                "tags": ["preflop", "aggression", "fundamental"],
                "prerequisites": ["VPIP"],
                "learning_objectives": [
                    "Understand the relationship between VPIP and PFR",
                    "Identify aggressive vs passive players",
                    "Use VPIP/PFR gaps to categorize opponents"
                ]
            },
            {
                "title": "Aggression Factor",
                "slug": "aggression-factor",
                "category": ContentCategory.BASIC,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "A measure of how aggressive a player is postflop, calculated as (Bets + Raises) / Calls.",
                "explanation": """Aggression Factor (AF) measures postflop aggression across all streets. It's calculated by dividing the total number of aggressive actions (bets and raises) by passive actions (calls).

AF = (Total Bets + Total Raises) / Total Calls

Typical ranges:
- Very passive: 0.5-1.0
- Somewhat passive: 1.0-2.0
- Balanced: 2.0-3.0
- Aggressive: 3.0-5.0
- Very aggressive: 5.0+

A higher AF indicates a player who prefers betting and raising over calling.""",
                "examples": [
                    "100 bets + 50 raises, 75 calls = AF of 2.0",
                    "AF of 4.0 means 4 aggressive actions for every call",
                    "Very low AF suggests a calling station"
                ],
                "related_stats": ["C-Bet %", "Check-Raise %", "VPIP", "PFR"],
                "tags": ["postflop", "aggression", "betting-patterns"],
                "prerequisites": ["VPIP", "PFR"],
                "learning_objectives": [
                    "Calculate and interpret Aggression Factor",
                    "Identify passive vs aggressive postflop players",
                    "Adjust strategy based on opponent's AF"
                ]
            },
            {
                "title": "Position in Poker",
                "slug": "position-in-poker",
                "category": ContentCategory.BASIC,
                "difficulty": DifficultyLevel.BEGINNER,
                "definition": "Your seat relative to the dealer button, determining the order of action.",
                "explanation": """Position is one of the most important concepts in poker. It determines when you act in each betting round, which provides significant strategic advantages.

Position categories (9-handed table):
- Early Position (EP): UTG, UTG+1, UTG+2
- Middle Position (MP): MP1, MP2
- Late Position (LP): Cutoff (CO), Button (BTN)
- Blinds: Small Blind (SB), Big Blind (BB)

Advantages of late position:
- See opponents' actions before deciding
- Control pot size
- Bluff more effectively
- Extract more value with strong hands""",
                "examples": [
                    "Button is the best position - acts last postflop",
                    "UTG is worst position - acts first on all streets",
                    "Play tighter ranges in early position"
                ],
                "related_stats": ["Position Stats", "VPIP by Position", "PFR by Position"],
                "tags": ["fundamental", "strategy", "preflop"],
                "prerequisites": [],
                "learning_objectives": [
                    "Understand position names and order",
                    "Recognize positional advantages",
                    "Adjust hand selection based on position"
                ]
            },
            {
                "title": "Pot Odds",
                "slug": "pot-odds",
                "category": ContentCategory.BASIC,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "The ratio of the current pot size to the cost of a call, used to determine if a call is profitable.",
                "explanation": """Pot odds help you make mathematically correct decisions by comparing the cost of calling to the potential reward.

Pot Odds = Cost to Call : Pot Size

To use pot odds:
1. Calculate the pot odds
2. Estimate your equity (chance of winning)
3. Call if your equity is greater than the pot odds

Example: $100 pot, $20 to call
Pot odds = 20:100 = 1:5 = 16.7%
You need at least 16.7% equity to call profitably.""",
                "examples": [
                    "$50 pot, $10 call = 1:6 odds (14.3% equity needed)",
                    "$200 pot, $50 call = 1:5 odds (16.7% equity needed)",
                    "Better pot odds = lower equity needed to call"
                ],
                "related_stats": ["Win Rate", "Expected Value"],
                "tags": ["mathematics", "decision-making", "fundamental"],
                "prerequisites": [],
                "learning_objectives": [
                    "Calculate pot odds quickly",
                    "Convert pot odds to percentages",
                    "Make profitable calling decisions"
                ]
            }
        ]

        await self._create_content_batch(basic_content)

    async def seed_advanced_content(self) -> None:
        """Seed advanced poker statistics content."""
        advanced_content = [
            {
                "title": "3-Bet Percentage",
                "slug": "three-bet-percentage",
                "category": ContentCategory.ADVANCED,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "The percentage of times a player re-raises (3-bets) when facing a preflop raise.",
                "explanation": """3-bet percentage measures preflop aggression when facing a raise. It's calculated as the number of 3-bets divided by the number of opportunities to 3-bet.

Typical 3-bet ranges:
- Tight players: 2-4%
- Balanced players: 5-8%
- Aggressive players: 9-12%+

3-betting serves multiple purposes:
- Build bigger pots with strong hands
- Apply pressure with bluffs
- Isolate weaker players
- Gain positional advantage""",
                "examples": [
                    "Face 100 raises, 3-bet 6 times = 6% 3-bet",
                    "Higher 3-bet % indicates aggressive player",
                    "Position affects optimal 3-bet frequency"
                ],
                "related_stats": ["PFR", "Fold to 3-Bet", "4-Bet %"],
                "tags": ["preflop", "aggression", "advanced"],
                "prerequisites": ["VPIP", "PFR"],
                "learning_objectives": [
                    "Understand 3-betting strategy",
                    "Identify optimal 3-bet frequencies",
                    "Adjust to opponents' 3-bet tendencies"
                ]
            },
            {
                "title": "C-Bet (Continuation Bet) Percentage",
                "slug": "c-bet-continuation-bet-percentage",
                "category": ContentCategory.ADVANCED,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "The percentage of times the preflop aggressor bets on the flop.",
                "explanation": """C-betting is when the player who raised preflop continues their aggression by betting the flop. It's a fundamental postflop concept.

Typical c-bet frequencies:
- Flop: 60-80%
- Turn: 45-65%
- River: 40-60%

Factors affecting c-bet frequency:
- Board texture (dry vs wet)
- Number of opponents
- Position
- Stack sizes
- Opponent tendencies

C-betting allows you to win pots immediately and build value with strong hands.""",
                "examples": [
                    "Raise preflop, bet flop = continuation bet",
                    "High c-bet % suggests aggressive postflop play",
                    "Board texture affects optimal c-bet frequency"
                ],
                "related_stats": ["Aggression Factor", "Fold to C-Bet", "Check-Raise %"],
                "tags": ["postflop", "aggression", "betting-patterns"],
                "prerequisites": ["PFR", "Aggression Factor"],
                "learning_objectives": [
                    "Understand c-betting strategy",
                    "Adjust c-bet frequency to board texture",
                    "Exploit opponents' c-bet tendencies"
                ]
            },
            {
                "title": "Red Line vs Blue Line",
                "slug": "red-line-vs-blue-line",
                "category": ContentCategory.ADVANCED,
                "difficulty": DifficultyLevel.ADVANCED,
                "definition": "Red line shows non-showdown winnings, blue line shows showdown winnings.",
                "explanation": """These lines help analyze your win rate sources:

Red Line (Non-showdown winnings):
- Money won without going to showdown
- Indicates bluffing success and fold equity
- Positive red line = good at making opponents fold

Blue Line (Showdown winnings):
- Money won at showdown
- Indicates hand reading and value betting
- Positive blue line = good at getting value

Total winnings = Red line + Blue line

Analyzing these lines helps identify leaks:
- Negative red line: Too passive, not bluffing enough
- Negative blue line: Poor hand reading or value betting""",
                "examples": [
                    "Strong red line = effective bluffing",
                    "Strong blue line = good value betting",
                    "Both lines together show complete picture"
                ],
                "related_stats": ["Win Rate", "Aggression Factor", "WTSD"],
                "tags": ["analysis", "advanced", "win-rate"],
                "prerequisites": ["Win Rate", "Aggression Factor"],
                "learning_objectives": [
                    "Understand red line vs blue line analysis",
                    "Identify strengths and weaknesses",
                    "Balance showdown and non-showdown winnings"
                ]
            }
        ]

        await self._create_content_batch(advanced_content)

    async def seed_tournament_content(self) -> None:
        """Seed tournament-specific content."""
        tournament_content = [
            {
                "title": "ICM (Independent Chip Model)",
                "slug": "icm-independent-chip-model",
                "category": ContentCategory.TOURNAMENT,
                "difficulty": DifficultyLevel.ADVANCED,
                "definition": "A mathematical model that calculates the real money value of tournament chips.",
                "explanation": """ICM converts tournament chips into real money equity based on payout structure and remaining players. It's crucial for tournament decision-making.

Key ICM concepts:
- Chip value decreases as you accumulate more
- Survival becomes more important near payouts
- Short stacks have ICM pressure
- Big stacks can apply ICM pressure

ICM affects strategy in:
- Bubble play
- Final table decisions
- Satellite tournaments
- Deal negotiations""",
                "examples": [
                    "10,000 chips ≠ $10,000 in tournament equity",
                    "Doubling chips doesn't double your equity",
                    "Bubble situations require tight play"
                ],
                "related_stats": ["M-Ratio", "Q-Ratio", "Bubble Factor"],
                "tags": ["tournament", "mathematics", "advanced"],
                "prerequisites": ["Tournament Basics"],
                "learning_objectives": [
                    "Understand ICM principles",
                    "Apply ICM to tournament decisions",
                    "Recognize ICM pressure situations"
                ]
            },
            {
                "title": "M-Ratio (Harrington's M)",
                "slug": "m-ratio-harrington-m",
                "category": ContentCategory.TOURNAMENT,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "The number of rounds you can survive paying blinds and antes without playing a hand.",
                "explanation": """M-Ratio measures your tournament life in terms of blind levels. It's calculated as:

M = Stack Size / (Small Blind + Big Blind + Antes)

M-Ratio zones:
- Green Zone (M > 20): Can play normal poker
- Yellow Zone (M 10-20): Tighten up, avoid marginal spots
- Orange Zone (M 6-10): Push/fold mode begins
- Red Zone (M 1-5): Desperate, must take risks
- Dead Zone (M < 1): All-in or fold only

Your M-Ratio determines your tournament strategy and available options.""",
                "examples": [
                    "5,000 chips, 100/200 blinds = M of 16.7",
                    "M of 8 means push/fold decisions",
                    "High M allows complex postflop play"
                ],
                "related_stats": ["ICM", "Q-Ratio", "Stack-to-Pot Ratio"],
                "tags": ["tournament", "stack-management", "strategy"],
                "prerequisites": ["Tournament Basics"],
                "learning_objectives": [
                    "Calculate M-Ratio quickly",
                    "Adjust strategy based on M-Ratio",
                    "Recognize critical M-Ratio thresholds"
                ]
            }
        ]

        await self._create_content_batch(tournament_content)

    async def seed_cash_game_content(self) -> None:
        """Seed cash game specific content."""
        cash_game_content = [
            {
                "title": "BB/100 (Big Blinds per 100 hands)",
                "slug": "bb-100-big-blinds-per-100-hands",
                "category": ContentCategory.CASH_GAME,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "A standardized measure of cash game win rate, showing big blinds won per 100 hands.",
                "explanation": """BB/100 is the standard way to measure cash game performance. It normalizes win rates across different stakes and allows for easy comparison.

Calculation: (Total Winnings in BB / Total Hands) × 100

Typical BB/100 rates:
- Losing players: Negative BB/100
- Break-even: 0-2 BB/100
- Small winners: 2-5 BB/100
- Good winners: 5-10 BB/100
- Exceptional: 10+ BB/100

BB/100 accounts for rake and provides a stake-independent measure of skill.""",
                "examples": [
                    "Win $500 in 1000 hands at $1/$2 = 25 BB/100",
                    "5 BB/100 is a solid win rate",
                    "Higher stakes typically have lower BB/100"
                ],
                "related_stats": ["Win Rate", "VPIP", "Red Line"],
                "tags": ["cash-game", "win-rate", "performance"],
                "prerequisites": ["Win Rate"],
                "learning_objectives": [
                    "Calculate BB/100 win rate",
                    "Understand typical win rate ranges",
                    "Track performance across stakes"
                ]
            },
            {
                "title": "Bankroll Management",
                "slug": "bankroll-management",
                "category": ContentCategory.CASH_GAME,
                "difficulty": DifficultyLevel.INTERMEDIATE,
                "definition": "The practice of managing your poker funds to minimize risk of ruin.",
                "explanation": """Bankroll management is crucial for long-term poker success. It involves having enough money to handle the natural variance in poker.

Standard bankroll requirements:
- Cash games: 20-40 buy-ins
- Tournaments: 50-100 buy-ins
- Sit & Go's: 30-50 buy-ins

Conservative players use higher requirements, aggressive players may use lower. The key is never playing above your bankroll limits.

Proper bankroll management:
- Prevents going broke during downswings
- Allows you to play your best game
- Reduces emotional stress
- Enables moving up stakes safely""",
                "examples": [
                    "$2,000 bankroll for $1/$2 cash games (20 buy-ins)",
                    "Move down stakes if bankroll drops",
                    "Never risk more than 5% in one session"
                ],
                "related_stats": ["Win Rate", "Standard Deviation", "Risk of Ruin"],
                "tags": ["cash-game", "bankroll", "risk-management"],
                "prerequisites": ["BB/100"],
                "learning_objectives": [
                    "Understand bankroll requirements",
                    "Implement proper bankroll management",
                    "Recognize when to move up or down stakes"
                ]
            }
        ]

        await self._create_content_batch(cash_game_content)

    async def _create_content_batch(self, content_list: List[Dict[str, Any]]) -> None:
        """Create a batch of education content."""
        for content_data in content_list:
            # Check if content already exists
            existing = await self.db.execute(
                select(EducationContent).where(EducationContent.slug == content_data["slug"])
            )
            if existing.scalar_one_or_none():
                continue  # Skip if already exists

            content = EducationContent(**content_data)
            self.db.add(content)

        await self.db.commit()


async def seed_education_content(db: AsyncSession) -> None:
    """Main function to seed all education content."""
    seeder = EducationContentSeeder(db)
    await seeder.seed_all_content()
    print("Education content seeded successfully!")