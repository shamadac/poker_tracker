#!/usr/bin/env python3
"""
Test all imports to ensure no import errors.
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    
    try:
        # Test core imports
        from app.core.config import settings
        print("✅ Core config import successful")
        
        # Test AI analysis service
        from app.services.ai_analysis import AIAnalysisService, AIProvider, AnalysisResult
        print("✅ AI analysis service import successful")
        
        # Test AI providers
        from app.services.ai_providers import AIProviderFactory, BaseAIClient, GeminiClient, GroqClient
        print("✅ AI providers import successful")
        
        # Test prompt manager
        from app.services.prompt_manager import get_prompt_manager, PromptManager
        print("✅ Prompt manager import successful")
        
        # Test schemas
        from app.schemas.hand import HandResponse
        from app.schemas.analysis import AnalysisResponse, HandAnalysisRequest, SessionAnalysisRequest
        print("✅ Schemas import successful")
        
        # Test API endpoints
        from app.api.v1.endpoints.analysis import router
        print("✅ Analysis endpoints import successful")
        
        # Test service instantiation
        ai_service = AIAnalysisService()
        print("✅ AI analysis service instantiation successful")
        
        # Test configuration access
        use_dev_keys = settings.USE_DEV_API_KEYS
        groq_key = settings.get_dev_api_key("groq")
        gemini_key = settings.get_dev_api_key("gemini")
        print(f"✅ Configuration access successful (dev keys: {use_dev_keys})")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ ALL IMPORTS SUCCESSFUL - NO ERRORS FOUND")
    else:
        print("\n❌ IMPORT ERRORS DETECTED")
    sys.exit(0 if success else 1)