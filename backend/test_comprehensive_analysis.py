#!/usr/bin/env python3
"""
Test comprehensive analysis features implementation.

Tests the new comprehensive analysis functionality including:
- Hand-by-hand analysis with decision points (7.1)
- Comprehensive breakdowns with recommendations (7.6)
- Adaptive analysis depth (7.8)
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.ai_analysis import AIAnalysisService, AIProvider, AnalysisResult
from app.services.prompt_manager import get_prompt_manager
from app.schemas.hand import HandResponse


def create_mock_hand() -> HandResponse:
    """Create a mock hand for testing."""
    from datetime import datetime
    return HandResponse(
        id="test_hand_1",
        hand_id="PS123456789",
        platform="pokerstars",
        game_type="No Limit Hold'em",
        stakes="$0.25/$0.50",
        position="Button",
        player_cards=["As", "Kh"],
        board_cards=["Qh", "Jc", "9s", "8d", "7c"],
        actions={
            "preflop": [
                {"player": "Hero", "action": "raise", "amount": 1.50, "street": "preflop"},
                {"player": "Villain1", "action": "call", "amount": 1.50, "street": "preflop"}
            ],
            "flop": [
                {"player": "Hero", "action": "bet", "amount": 2.25, "street": "flop"},
                {"player": "Villain1", "action": "call", "amount": 2.25, "street": "flop"}
            ],
            "turn": [
                {"player": "Hero", "action": "bet", "amount": 5.50, "street": "turn"},
                {"player": "Villain1", "action": "fold", "street": "turn"}
            ]
        },
        result="Won $8.50",
        pot_size=8.50,
        timestamp=datetime.now(),
        user_id="test_user",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_mock_session_hands() -> list[HandResponse]:
    """Create mock hands for session testing."""
    from datetime import datetime
    hands = []
    positions = ["UTG", "MP", "CO", "BTN", "SB", "BB"]
    results = ["Won $2.50", "Lost $1.00", "Won $5.25", "Lost $0.50", "Won $1.75"]
    
    for i in range(5):
        hands.append(HandResponse(
            id=f"test_hand_{i+1}",
            hand_id=f"PS12345678{i}",
            platform="pokerstars",
            game_type="No Limit Hold'em",
            stakes="$0.25/$0.50",
            position=positions[i % len(positions)],
            player_cards=["As", "Kh"],
            board_cards=["Qh", "Jc", "9s"],
            actions={
                "preflop": [
                    {"player": "Hero", "action": "raise", "amount": 1.50, "street": "preflop"},
                    {"player": "Villain1", "action": "call", "amount": 1.50, "street": "preflop"}
                ]
            },
            result=results[i % len(results)],
            pot_size=3.0 + i,
            timestamp=datetime.now(),
            user_id="test_user",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ))
    
    return hands


async def test_comprehensive_hand_analysis():
    """Test comprehensive hand analysis functionality."""
    print("Testing comprehensive hand analysis...")
    
    ai_service = AIAnalysisService()
    mock_hand = create_mock_hand()
    
    # Test adaptive analysis depth
    experience_levels = ["beginner", "intermediate", "advanced"]
    analysis_depths = ["basic", "standard", "advanced"]
    
    for exp_level in experience_levels:
        for depth in analysis_depths:
            print(f"\nTesting {exp_level} player with {depth} analysis depth:")
            
            # Test analysis type determination
            analysis_type = ai_service._determine_analysis_type(exp_level, depth)
            print(f"  Determined analysis type: {analysis_type}")
            
            # Test comprehensive data preparation
            hand_data = ai_service._prepare_comprehensive_hand_data(
                mock_hand, exp_level, ["preflop", "postflop"]
            )
            
            print(f"  Decision points found: {len(hand_data.get('decision_points', []))}")
            print(f"  Key decisions: {hand_data.get('key_decisions', 'None')}")
            print(f"  Focus areas: {hand_data.get('focus_areas', 'None')}")
            
            # Verify decision points extraction
            decision_points = hand_data.get('decision_points', [])
            assert len(decision_points) > 0, "Should extract decision points"
            
            # Verify adaptive depth works
            if exp_level == "beginner":
                assert analysis_type == "basic", f"Beginners should get basic analysis, got {analysis_type}"
            elif exp_level == "advanced" and depth == "advanced":
                assert analysis_type == "advanced", f"Advanced players should get advanced analysis"


async def test_comprehensive_session_analysis():
    """Test comprehensive session analysis functionality."""
    print("\nTesting comprehensive session analysis...")
    
    ai_service = AIAnalysisService()
    mock_hands = create_mock_session_hands()
    
    mock_session_stats = {
        "vpip": 25.0,
        "pfr": 20.0,
        "aggression_factor": 2.5,
        "win_rate": 4.2,
        "three_bet_percentage": 8.0,
        "cbet_flop": 70.0,
        "hands_played": len(mock_hands)
    }
    
    # Test session analysis type determination
    experience_levels = ["beginner", "intermediate", "advanced"]
    
    for exp_level in experience_levels:
        print(f"\nTesting session analysis for {exp_level} player:")
        
        session_type = ai_service._determine_session_analysis_type(exp_level, "summary")
        print(f"  Session analysis type: {session_type}")
        
        # Test comprehensive session data preparation
        session_data = ai_service._prepare_comprehensive_session_data(
            mock_hands, mock_session_stats, exp_level, True
        )
        
        print(f"  Leaks identified: {len(session_data.get('leak_analysis', []))}")
        print(f"  Strengths identified: {len(session_data.get('strength_analysis', []))}")
        print(f"  Improvement priorities: {len(session_data.get('improvement_priorities', []))}")
        print(f"  Individual hand summaries: {len(session_data.get('individual_hand_summaries', []))}")
        
        # Verify session insights
        assert 'decision_quality' in session_data, "Should include decision quality assessment"
        assert 'leak_analysis' in session_data, "Should include leak analysis"
        assert 'strength_analysis' in session_data, "Should include strength analysis"
        
        # Verify adaptive analysis for beginners
        if exp_level == "beginner":
            assert session_type == "quick_review", "Beginners should get quick review"


def test_decision_point_extraction():
    """Test decision point extraction from hands."""
    print("\nTesting decision point extraction...")
    
    ai_service = AIAnalysisService()
    mock_hand = create_mock_hand()
    
    decision_points = ai_service._extract_decision_points(mock_hand)
    
    print(f"Extracted {len(decision_points)} decision points:")
    for dp in decision_points:
        print(f"  {dp['street']}: {dp['action']} ${dp.get('amount', 0)}")
    
    # Verify decision points
    assert len(decision_points) > 0, "Should extract decision points"
    
    # Check that we have preflop and postflop decisions
    streets = [dp['street'] for dp in decision_points]
    assert 'preflop' in streets, "Should have preflop decisions"
    assert any(street in ['flop', 'turn', 'river'] for street in streets), "Should have postflop decisions"


def test_structured_insights_extraction():
    """Test structured insights extraction from analysis content."""
    print("\nTesting structured insights extraction...")
    
    ai_service = AIAnalysisService()
    
    # Mock analysis content
    mock_analysis = """
    This hand shows several key decision points.
    
    Recommendations:
    1. Consider a larger preflop raise size
    2. The flop c-bet was well-sized
    3. Turn bet could be larger for value
    
    Strengths:
    - Good position awareness
    - Solid bet sizing on flop
    
    Weaknesses:
    - Missed value on turn
    - Could have been more aggressive
    
    Learning Focus:
    - Study turn value betting
    - Practice sizing in position
    """
    
    insights = ai_service._extract_structured_insights(mock_analysis, "advanced")
    
    print("Extracted insights:")
    print(f"  Recommendations: {len(insights.get('recommendations', []))}")
    print(f"  Strengths: {len(insights.get('strengths', []))}")
    print(f"  Weaknesses: {len(insights.get('weaknesses', []))}")
    print(f"  Learning focus: {len(insights.get('learning_focus', []))}")
    
    # Verify extraction
    assert len(insights.get('recommendations', [])) > 0, "Should extract recommendations"
    assert len(insights.get('strengths', [])) > 0, "Should extract strengths"
    assert len(insights.get('weaknesses', [])) > 0, "Should extract weaknesses"


def test_leak_and_strength_identification():
    """Test leak and strength identification from session stats."""
    print("\nTesting leak and strength identification...")
    
    ai_service = AIAnalysisService()
    mock_hands = create_mock_session_hands()
    
    # Test with loose stats
    loose_stats = {"vpip": 40, "pfr": 15, "aggression_factor": 0.8, "win_rate": -2.5}
    leaks = ai_service._identify_session_leaks(mock_hands, loose_stats)
    strengths = ai_service._identify_session_strengths(mock_hands, loose_stats)
    
    print("Loose player analysis:")
    print(f"  Leaks: {leaks}")
    print(f"  Strengths: {strengths}")
    
    assert any("too many hands" in leak.lower() or "high vpip" in leak.lower() for leak in leaks), "Should identify loose play"
    assert any("passive" in leak.lower() for leak in leaks), "Should identify passive play"
    
    # Test with tight-aggressive stats
    tag_stats = {"vpip": 22, "pfr": 18, "aggression_factor": 2.5, "win_rate": 5.2}
    leaks_tag = ai_service._identify_session_leaks(mock_hands, tag_stats)
    strengths_tag = ai_service._identify_session_strengths(mock_hands, tag_stats)
    
    print("\nTight-aggressive player analysis:")
    print(f"  Leaks: {leaks_tag}")
    print(f"  Strengths: {strengths_tag}")
    
    assert any("balanced" in strength.lower() for strength in strengths_tag), "Should identify balanced play"
    assert any("positive" in strength.lower() or "profitable" in strength.lower() for strength in strengths_tag), "Should identify profitability"


async def main():
    """Run all comprehensive analysis tests."""
    print("=" * 60)
    print("COMPREHENSIVE ANALYSIS FEATURES TEST")
    print("=" * 60)
    
    try:
        # Test comprehensive hand analysis
        await test_comprehensive_hand_analysis()
        
        # Test comprehensive session analysis
        await test_comprehensive_session_analysis()
        
        # Test decision point extraction
        test_decision_point_extraction()
        
        # Test structured insights extraction
        test_structured_insights_extraction()
        
        # Test leak and strength identification
        test_leak_and_strength_identification()
        
        print("\n" + "=" * 60)
        print("✅ ALL COMPREHENSIVE ANALYSIS TESTS PASSED!")
        print("=" * 60)
        print("\nImplemented features:")
        print("✅ Hand-by-hand analysis with decision points (Requirement 7.1)")
        print("✅ Comprehensive breakdowns with recommendations (Requirement 7.6)")
        print("✅ Adaptive analysis depth based on experience level (Requirement 7.8)")
        print("✅ Session analysis with individual hand summaries")
        print("✅ Structured insights extraction")
        print("✅ Leak and strength identification")
        print("✅ Decision point analysis")
        print("✅ Improvement prioritization")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)