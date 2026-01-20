#!/usr/bin/env python3
"""
Test AI analysis with real hand history data.

This test parses actual hand history files and shows what the AI returns
for comprehensive analysis.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.ai_analysis import get_ai_analysis_service, AIProvider
from app.services.hand_parser import HandParserService
from app.schemas.hand import HandResponse


async def test_real_hand_analysis():
    """Test AI analysis with real hand history data."""
    print("=" * 60)
    print("REAL HAND ANALYSIS TEST WITH AI")
    print("=" * 60)
    
    # Find sample hand history files
    sample_files = [
        "../sample_data/HH20260114_Z420909_real.txt",
        "../sample_data/HH20260112_Z420909_playmoney.txt"
    ]
    
    ai_service = get_ai_analysis_service()
    hand_parser = HandParserService()
    
    for file_path in sample_files:
        if not Path(file_path).exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        print(f"\n📁 Processing file: {file_path}")
        print("-" * 50)
        
        try:
            # Read and parse the hand history file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse hands from the file
            parsed_hands = await hand_parser.parse_pokerstars_file(content)
            
            if not parsed_hands:
                print("❌ No hands found in file")
                continue
            
            print(f"✅ Found {len(parsed_hands)} hands in file")
            
            # Take the first interesting hand for analysis
            test_hand = None
            for hand in parsed_hands:
                # Look for a hand with some action (not just folds)
                if hand.actions and len(hand.actions) > 2:
                    test_hand = hand
                    break
            
            if not test_hand:
                test_hand = parsed_hands[0]  # Use first hand if no complex ones
            
            print(f"\n🎯 Analyzing hand: {test_hand.hand_id}")
            print(f"   Position: {test_hand.position}")
            print(f"   Cards: {test_hand.player_cards}")
            print(f"   Board: {test_hand.board_cards}")
            print(f"   Result: {test_hand.result}")
            
            # Convert to HandResponse for AI analysis
            hand_response = HandResponse(
                id=test_hand.hand_id,
                hand_id=test_hand.hand_id,
                platform=test_hand.platform,
                game_type=test_hand.game_type,
                stakes=test_hand.stakes,
                position=test_hand.position,
                player_cards=test_hand.player_cards,
                board_cards=test_hand.board_cards,
                actions=test_hand.actions,
                result=test_hand.result,
                pot_size=test_hand.pot_size,
                user_id="test_user",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Test with both AI providers
            providers = [AIProvider.GROQ, AIProvider.GEMINI]
            
            for provider in providers:
                print(f"\n🤖 Testing {provider.value.upper()} Analysis:")
                print("=" * 40)
                
                try:
                    # Comprehensive analysis
                    result = await ai_service.analyze_hand_comprehensive(
                        hand=hand_response,
                        provider=provider,
                        api_key="",  # Use dev keys
                        experience_level="intermediate",
                        analysis_depth="standard",
                        focus_areas=["preflop", "postflop"]
                    )
                    
                    if result.success:
                        print(f"✅ {provider.value} Analysis SUCCESS")
                        print(f"📊 Analysis Length: {len(result.content)} characters")
                        print(f"🔧 Used Dev Key: {result.metadata.get('used_dev_key', False)}")
                        print(f"🎯 Analysis Type: {result.metadata.get('analysis_type', 'unknown')}")
                        
                        # Show first part of analysis
                        print(f"\n📝 Analysis Preview:")
                        print("-" * 30)
                        preview = result.content[:500] + "..." if len(result.content) > 500 else result.content
                        print(preview)
                        
                        # Show structured insights if available
                        insights = result.metadata.get('structured_insights', {})
                        if insights:
                            print(f"\n🎯 Structured Insights:")
                            for key, value in insights.items():
                                if value:
                                    print(f"   {key}: {len(value)} items")
                        
                        print(f"\n💰 API Usage:")
                        if result.usage:
                            for key, value in result.usage.items():
                                print(f"   {key}: {value}")
                        
                    else:
                        print(f"❌ {provider.value} Analysis FAILED")
                        print(f"   Error: {result.error}")
                
                except Exception as e:
                    print(f"❌ {provider.value} Analysis ERROR: {e}")
            
            # Only analyze first file for detailed output
            break
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    print("\n" + "=" * 60)
    print("REAL HAND ANALYSIS TEST COMPLETE")
    print("=" * 60)


async def test_educational_content():
    """Test educational content generation."""
    print("\n" + "=" * 60)
    print("EDUCATIONAL CONTENT TEST")
    print("=" * 60)
    
    ai_service = get_ai_analysis_service()
    
    concepts = ["VPIP", "Position", "Pot Odds"]
    
    for concept in concepts:
        print(f"\n📚 Testing educational content for: {concept}")
        print("-" * 40)
        
        try:
            result = await ai_service.get_educational_content(
                concept=concept,
                provider=AIProvider.GROQ,  # Use Groq for speed
                api_key="",  # Use dev keys
                experience_level="beginner",
                context="Learning poker fundamentals"
            )
            
            if result.success:
                print(f"✅ Educational content generated")
                print(f"📊 Content Length: {len(result.content)} characters")
                
                # Show preview
                preview = result.content[:300] + "..." if len(result.content) > 300 else result.content
                print(f"\n📝 Content Preview:")
                print("-" * 20)
                print(preview)
            else:
                print(f"❌ Failed to generate content: {result.error}")
        
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all tests."""
    await test_real_hand_analysis()
    await test_educational_content()


if __name__ == "__main__":
    asyncio.run(main())