#!/usr/bin/env python3
"""
Test AI analysis with sample poker hand data.

This test creates realistic hand data and shows what the AI returns
for comprehensive analysis.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.ai_analysis import get_ai_analysis_service, AIProvider
from app.schemas.hand import HandResponse


def create_sample_hands():
    """Create sample poker hands for testing."""
    
    # Hand 1: Aggressive preflop play with continuation bet
    hand1 = HandResponse(
        id="test_hand_1",
        hand_id="PS259309834385",
        platform="pokerstars",
        game_type="No Limit Hold'em",
        stakes="$0.02/$0.05",
        position="Button",
        player_cards=["As", "Kh"],
        board_cards=["Qh", "Jc", "9s"],
        actions={
            "preflop": [
                {"player": "Hero", "action": "raise", "amount": 0.15, "street": "preflop"},
                {"player": "Villain1", "action": "call", "amount": 0.15, "street": "preflop"},
                {"player": "Villain2", "action": "call", "amount": 0.15, "street": "preflop"}
            ],
            "flop": [
                {"player": "Hero", "action": "bet", "amount": 0.35, "street": "flop"},
                {"player": "Villain1", "action": "fold", "street": "flop"},
                {"player": "Villain2", "action": "call", "amount": 0.35, "street": "flop"}
            ],
            "turn": [
                {"player": "Hero", "action": "bet", "amount": 0.80, "street": "turn"},
                {"player": "Villain2", "action": "fold", "street": "turn"}
            ]
        },
        result="Won $1.25",
        pot_size=1.25,
        user_id="test_user",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Hand 2: Tricky spot with marginal hand
    hand2 = HandResponse(
        id="test_hand_2",
        hand_id="PS259309846007",
        platform="pokerstars",
        game_type="No Limit Hold'em",
        stakes="$0.02/$0.05",
        position="Big Blind",
        player_cards=["8h", "2d"],
        board_cards=["2s", "9d", "5d"],
        actions={
            "preflop": [
                {"player": "Villain1", "action": "call", "amount": 0.05, "street": "preflop"},
                {"player": "Hero", "action": "check", "amount": 0, "street": "preflop"},
                {"player": "Villain2", "action": "call", "amount": 0.05, "street": "preflop"}
            ],
            "flop": [
                {"player": "Hero", "action": "bet", "amount": 0.12, "street": "flop"},
                {"player": "Villain1", "action": "fold", "street": "flop"},
                {"player": "Villain2", "action": "fold", "street": "flop"}
            ]
        },
        result="Won $0.24",
        pot_size=0.24,
        user_id="test_user",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Hand 3: Tournament spot with short stack
    hand3 = HandResponse(
        id="test_hand_3",
        hand_id="PS259309857123",
        platform="pokerstars",
        game_type="Tournament Hold'em",
        stakes="$5+$0.50",
        position="Small Blind",
        player_cards=["Ah", "Qc"],
        board_cards=["Kh", "Jd", "Tc", "9s", "2h"],
        actions={
            "preflop": [
                {"player": "Hero", "action": "raise", "amount": 600, "street": "preflop"},
                {"player": "Villain1", "action": "call", "amount": 600, "street": "preflop"}
            ],
            "flop": [
                {"player": "Hero", "action": "bet", "amount": 800, "street": "flop"},
                {"player": "Villain1", "action": "call", "amount": 800, "street": "flop"}
            ],
            "turn": [
                {"player": "Hero", "action": "check", "street": "turn"},
                {"player": "Villain1", "action": "bet", "amount": 1200, "street": "turn"},
                {"player": "Hero", "action": "call", "amount": 1200, "street": "turn"}
            ],
            "river": [
                {"player": "Hero", "action": "check", "street": "river"},
                {"player": "Villain1", "action": "check", "street": "river"}
            ]
        },
        result="Won 5400 chips (straight)",
        pot_size=5400,
        user_id="test_user",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return [hand1, hand2, hand3]


async def test_comprehensive_hand_analysis():
    """Test comprehensive hand analysis with sample data."""
    print("=" * 70)
    print("COMPREHENSIVE HAND ANALYSIS TEST WITH REAL AI")
    print("=" * 70)
    
    ai_service = get_ai_analysis_service()
    sample_hands = create_sample_hands()
    
    providers = [AIProvider.GROQ, AIProvider.GEMINI]
    
    for i, hand in enumerate(sample_hands, 1):
        print(f"\n🎯 HAND {i}: {hand.hand_id}")
        print(f"   Position: {hand.position}")
        print(f"   Cards: {' '.join(hand.player_cards)}")
        print(f"   Board: {' '.join(hand.board_cards) if hand.board_cards else 'N/A'}")
        print(f"   Result: {hand.result}")
        print("=" * 50)
        
        for provider in providers:
            print(f"\n🤖 {provider.value.upper()} ANALYSIS:")
            print("-" * 30)
            
            try:
                result = await ai_service.analyze_hand_comprehensive(
                    hand=hand,
                    provider=provider,
                    api_key="",  # Use dev keys
                    experience_level="intermediate",
                    analysis_depth="standard",
                    focus_areas=["preflop", "postflop", "decision_making"]
                )
                
                if result.success:
                    print(f"✅ SUCCESS - Analysis generated")
                    print(f"📊 Length: {len(result.content)} characters")
                    print(f"🔧 Used Dev Key: {result.metadata.get('used_dev_key', False)}")
                    
                    # Show the actual AI analysis
                    print(f"\n📝 AI ANALYSIS:")
                    print("=" * 40)
                    print(result.content)
                    print("=" * 40)
                    
                    # Show structured insights
                    insights = result.metadata.get('structured_insights', {})
                    if insights:
                        print(f"\n🎯 STRUCTURED INSIGHTS:")
                        for key, items in insights.items():
                            if items:
                                print(f"\n{key.upper()}:")
                                for item in items[:3]:  # Show first 3 items
                                    print(f"  • {item}")
                    
                    # Show usage stats
                    if result.usage:
                        print(f"\n💰 API USAGE:")
                        for key, value in result.usage.items():
                            print(f"   {key}: {value}")
                
                else:
                    print(f"❌ FAILED: {result.error}")
            
            except Exception as e:
                print(f"❌ ERROR: {e}")
        
        # Only analyze first hand in detail to avoid too much output
        if i == 1:
            break


async def test_session_analysis():
    """Test session analysis with multiple hands."""
    print(f"\n{'=' * 70}")
    print("SESSION ANALYSIS TEST")
    print("=" * 70)
    
    ai_service = get_ai_analysis_service()
    sample_hands = create_sample_hands()
    
    # Mock session statistics
    session_stats = {
        "vpip": 28.5,
        "pfr": 22.0,
        "aggression_factor": 2.8,
        "win_rate": 4.2,
        "three_bet_percentage": 12.5,
        "cbet_flop": 68.0,
        "hands_played": len(sample_hands)
    }
    
    print(f"📊 Session Stats: {len(sample_hands)} hands")
    print(f"   VPIP: {session_stats['vpip']}%")
    print(f"   PFR: {session_stats['pfr']}%")
    print(f"   Aggression: {session_stats['aggression_factor']}")
    print(f"   Win Rate: {session_stats['win_rate']} BB/100")
    
    try:
        result = await ai_service.analyze_session_comprehensive(
            hands=sample_hands,
            session_stats=session_stats,
            provider=AIProvider.GROQ,  # Use Groq for speed
            api_key="",  # Use dev keys
            analysis_type="summary",
            experience_level="intermediate",
            include_individual_hands=True
        )
        
        if result.success:
            print(f"\n✅ SESSION ANALYSIS SUCCESS")
            print(f"📊 Analysis Length: {len(result.content)} characters")
            
            print(f"\n📝 SESSION ANALYSIS:")
            print("=" * 50)
            print(result.content)
            print("=" * 50)
            
            # Show session insights
            insights = result.metadata.get('structured_insights', {})
            if insights:
                print(f"\n🎯 SESSION INSIGHTS:")
                for key, items in insights.items():
                    if items:
                        print(f"\n{key.upper()}:")
                        # Handle session_summary as a string, others as lists
                        if key == 'session_summary':
                            print(f"  {items}")
                        else:
                            # Handle as list
                            if isinstance(items, list):
                                for item in items:
                                    print(f"  • {item}")
                            else:
                                print(f"  • {items}")
        
        else:
            print(f"❌ SESSION ANALYSIS FAILED: {result.error}")
    
    except Exception as e:
        print(f"❌ SESSION ANALYSIS ERROR: {e}")


async def test_educational_content():
    """Test educational content generation."""
    print(f"\n{'=' * 70}")
    print("EDUCATIONAL CONTENT TEST")
    print("=" * 70)
    
    ai_service = get_ai_analysis_service()
    
    concepts = ["VPIP", "Position Play", "Continuation Betting"]
    
    for concept in concepts:
        print(f"\n📚 Educational Content: {concept}")
        print("-" * 40)
        
        try:
            result = await ai_service.get_educational_content(
                concept=concept,
                provider=AIProvider.GROQ,
                api_key="",  # Use dev keys
                experience_level="beginner",
                context="Learning fundamental poker concepts"
            )
            
            if result.success:
                print(f"✅ Content generated ({len(result.content)} chars)")
                
                print(f"\n📝 EDUCATIONAL CONTENT:")
                print("=" * 30)
                print(result.content)
                print("=" * 30)
            
            else:
                print(f"❌ Failed: {result.error}")
        
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all tests."""
    await test_comprehensive_hand_analysis()
    await test_session_analysis()
    await test_educational_content()
    
    print(f"\n{'=' * 70}")
    print("ALL AI TESTS COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())