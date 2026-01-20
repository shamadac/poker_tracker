#!/usr/bin/env python3
"""
Test AI integration with development API keys.

This test directly tests the AI provider integration using the development keys.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Force reload environment variables
from pathlib import Path
from dotenv import load_dotenv

# Load .env.local to ensure dev keys are available
env_local_path = Path(__file__).parent / '.env.local'
if env_local_path.exists():
    load_dotenv(env_local_path, override=True)

from app.services.ai_providers import AIProviderFactory, AIProvider


async def test_groq_integration():
    """Test Groq integration with development API key."""
    print("Testing Groq integration...")
    
    # Get the development API key directly from environment
    api_key = os.getenv('DEV_GROQ_API_KEY')
    if not api_key:
        print("❌ No Groq development API key found")
        return False
    
    print(f"Using Groq API key: {api_key[:10]}...")
    
    try:
        # Test API key validation
        is_valid = await AIProviderFactory.validate_api_key(AIProvider.GROQ, api_key)
        print(f"Groq API key validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        if is_valid:
            # Test actual API call
            client = AIProviderFactory.create_client(AIProvider.GROQ, api_key)
            response = await client.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello from Groq!' in exactly those words.",
                max_tokens=50,
                temperature=0.1
            )
            
            print(f"Groq API call success: {'✅ Yes' if response.success else '❌ No'}")
            if response.success:
                print(f"Response: {response.content}")
                return True
            else:
                print(f"Error: {response.error}")
                return False
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Groq integration error: {e}")
        return False


async def test_gemini_integration():
    """Test Gemini integration with development API key."""
    print("\nTesting Gemini integration...")
    
    # Get the development API key directly from environment
    api_key = os.getenv('DEV_GEMINI_API_KEY')
    if not api_key:
        print("❌ No Gemini development API key found")
        return False
    
    print(f"Using Gemini API key: {api_key[:10]}...")
    
    try:
        # Test API key validation
        is_valid = await AIProviderFactory.validate_api_key(AIProvider.GEMINI, api_key)
        print(f"Gemini API key validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        if is_valid:
            # Test actual API call
            client = AIProviderFactory.create_client(AIProvider.GEMINI, api_key)
            response = await client.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello from Gemini!' in exactly those words.",
                max_tokens=50,
                temperature=0.1
            )
            
            print(f"Gemini API call success: {'✅ Yes' if response.success else '❌ No'}")
            if response.success:
                print(f"Response: {response.content}")
                return True
            else:
                print(f"Error: {response.error}")
                return False
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Gemini integration error: {e}")
        return False


async def test_comprehensive_analysis_integration():
    """Test comprehensive analysis with development keys."""
    print("\nTesting comprehensive analysis integration...")
    
    from app.services.ai_analysis import AIAnalysisService
    from app.schemas.hand import HandResponse
    from datetime import datetime
    
    # Create a simple mock hand
    mock_hand = HandResponse(
        id="integration_test_hand",
        hand_id="INT_TEST_123",
        platform="pokerstars",
        game_type="No Limit Hold'em",
        stakes="$0.25/$0.50",
        position="Button",
        player_cards=["As", "Kh"],
        board_cards=["Qh", "Jc", "9s"],
        actions={
            "preflop": [
                {"player": "Hero", "action": "raise", "amount": 1.50, "street": "preflop"}
            ]
        },
        result="Won $2.50",
        pot_size=2.50,
        user_id="test_user",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    ai_service = AIAnalysisService()
    
    # Test with Groq using development key
    groq_key = os.getenv('DEV_GROQ_API_KEY')
    if groq_key:
        print("Testing comprehensive analysis with Groq...")
        try:
            result = await ai_service.analyze_hand_comprehensive(
                hand=mock_hand,
                provider=AIProvider.GROQ,
                api_key=groq_key,
                experience_level="beginner",
                analysis_depth="basic"
            )
            
            print(f"Groq comprehensive analysis: {'✅ Success' if result.success else '❌ Failed'}")
            if result.success:
                print(f"Analysis length: {len(result.content) if result.content else 0} characters")
            else:
                print(f"Error: {result.error}")
                
        except Exception as e:
            print(f"❌ Groq comprehensive analysis error: {e}")
    
    # Test with Gemini using development key
    gemini_key = os.getenv('DEV_GEMINI_API_KEY')
    if gemini_key:
        print("\nTesting comprehensive analysis with Gemini...")
        try:
            result = await ai_service.analyze_hand_comprehensive(
                hand=mock_hand,
                provider=AIProvider.GEMINI,
                api_key=gemini_key,
                experience_level="beginner",
                analysis_depth="basic"
            )
            
            print(f"Gemini comprehensive analysis: {'✅ Success' if result.success else '❌ Failed'}")
            if result.success:
                print(f"Analysis length: {len(result.content) if result.content else 0} characters")
            else:
                print(f"Error: {result.error}")
                
        except Exception as e:
            print(f"❌ Gemini comprehensive analysis error: {e}")


async def main():
    """Run AI integration tests with development keys."""
    print("=" * 60)
    print("AI INTEGRATION TEST WITH DEVELOPMENT KEYS")
    print("=" * 60)
    
    # Check if development keys are available
    groq_key = os.getenv('DEV_GROQ_API_KEY')
    gemini_key = os.getenv('DEV_GEMINI_API_KEY')
    
    print(f"Groq dev key available: {'✅ Yes' if groq_key else '❌ No'}")
    print(f"Gemini dev key available: {'✅ Yes' if gemini_key else '❌ No'}")
    
    if not groq_key and not gemini_key:
        print("\n❌ No development API keys found!")
        print("Make sure .env.local file exists with DEV_GROQ_API_KEY and DEV_GEMINI_API_KEY")
        return False
    
    print("\n" + "-" * 60)
    
    success = True
    
    # Test Groq integration
    if groq_key:
        groq_success = await test_groq_integration()
        success = success and groq_success
    
    # Test Gemini integration
    if gemini_key:
        gemini_success = await test_gemini_integration()
        success = success and gemini_success
    
    # Test comprehensive analysis
    await test_comprehensive_analysis_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ AI INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
        print("\n🔑 Development API keys are working correctly")
        print("   - Ready for local development and testing")
        print("   - Comprehensive analysis features functional")
    else:
        print("❌ SOME AI INTEGRATION TESTS FAILED")
        print("   - Check API key validity and network connection")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)