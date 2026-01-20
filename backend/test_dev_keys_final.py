#!/usr/bin/env python3
"""
Final test of development API keys with proper environment loading.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env.local to ensure dev keys are available
env_local_path = Path(__file__).parent / '.env.local'
if env_local_path.exists():
    load_dotenv(env_local_path, override=True)

# Now import and test
from app.core.config import settings
from app.services.ai_analysis import AIAnalysisService, AIProvider

def test_dev_keys_with_proper_loading():
    """Test development keys with proper environment loading."""
    print("Testing development API keys with proper loading...")
    
    # Check environment variables directly
    use_dev_keys = os.getenv('USE_DEV_API_KEYS', 'false').lower() == 'true'
    groq_key = os.getenv('DEV_GROQ_API_KEY', '')
    gemini_key = os.getenv('DEV_GEMINI_API_KEY', '')
    
    print(f"Environment USE_DEV_API_KEYS: {use_dev_keys}")
    print(f"Environment DEV_GROQ_API_KEY: {'Present' if groq_key else 'Missing'}")
    print(f"Environment DEV_GEMINI_API_KEY: {'Present' if gemini_key else 'Missing'}")
    
    # Check settings
    print(f"Settings USE_DEV_API_KEYS: {settings.USE_DEV_API_KEYS}")
    print(f"Settings DEV_GROQ_API_KEY: {'Present' if settings.DEV_GROQ_API_KEY else 'Missing'}")
    print(f"Settings DEV_GEMINI_API_KEY: {'Present' if settings.DEV_GEMINI_API_KEY else 'Missing'}")
    
    # Test API key resolution
    ai_service = AIAnalysisService()
    
    # Test with empty user key (should use dev key if available)
    groq_resolved = ai_service._get_api_key(AIProvider.GROQ, "")
    gemini_resolved = ai_service._get_api_key(AIProvider.GEMINI, "")
    
    print(f"Groq key resolved: {'Yes' if groq_resolved else 'No'}")
    print(f"Gemini key resolved: {'Yes' if gemini_resolved else 'No'}")
    
    if use_dev_keys and groq_key and gemini_key:
        assert groq_resolved, "Groq key should be resolved from dev settings"
        assert gemini_resolved, "Gemini key should be resolved from dev settings"
        print("✅ Development API keys are working correctly")
        return True
    else:
        print("ℹ️  Development API keys are not configured or disabled")
        return True

if __name__ == "__main__":
    success = test_dev_keys_with_proper_loading()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: Development API key test completed")