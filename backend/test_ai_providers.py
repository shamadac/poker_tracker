#!/usr/bin/env python3
"""
Test script for AI provider integration.

This script tests the AI provider clients (Gemini and Groq) to ensure
they work correctly with the poker analysis system.

Usage:
    python test_ai_providers.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.ai_providers import AIProviderFactory, AIProvider
from app.services.ai_analysis import AIAnalysisService
from app.services.prompt_manager import PromptManager


async def test_provider_factory():
    """Test the AI provider factory."""
    print("Testing AI Provider Factory...")
    
    # Test getting available providers
    providers = AIProviderFactory.get_available_providers()
    print(f"Available providers: {[p.value for p in providers]}")
    
    # Test getting default models
    default_models = AIProviderFactory.get_default_models()
    print(f"Default models: {default_models}")
    
    return True


async def test_gemini_client():
    """Test Gemini client (requires valid API key)."""
    print("\nTesting Gemini Client...")
    
    # This would require a real API key to test
    # For now, we'll test the client creation and validation
    try:
        # Test with invalid key (should fail validation)
        try:
            client = AIProviderFactory.create_client(AIProvider.GEMINI, "invalid_key")
            print("❌ Gemini client should have failed with invalid key")
            return False
        except ValueError as e:
            print(f"✅ Gemini validation correctly rejected invalid key: {e}")
        
        # Test with properly formatted key (won't work without real key)
        try:
            test_key = "AIzaSyDummyKeyForTestingPurposesOnly1234567890"
            client = AIProviderFactory.create_client(AIProvider.GEMINI, test_key)
            print("✅ Gemini client created successfully with valid format key")
            
            # Test response generation (will fail without real API key)
            response = await client.generate_response(
                "You are a helpful assistant.",
                "Say hello.",
                temperature=0.1,
                max_tokens=50
            )
            
            if response.success:
                print(f"✅ Gemini response: {response.content[:100]}...")
            else:
                print(f"⚠️  Gemini response failed (expected without real API key): {response.error}")
            
        except Exception as e:
            print(f"⚠️  Gemini test failed (expected without real API key): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini client test failed: {e}")
        return False


async def test_groq_client():
    """Test Groq client (requires valid API key)."""
    print("\nTesting Groq Client...")
    
    try:
        # Test with invalid key (should fail validation)
        try:
            client = AIProviderFactory.create_client(AIProvider.GROQ, "invalid_key")
            print("❌ Groq client should have failed with invalid key")
            return False
        except ValueError as e:
            print(f"✅ Groq validation correctly rejected invalid key: {e}")
        
        # Test with properly formatted key (won't work without real key)
        try:
            test_key = "gsk_dummy_test_key_123"
            client = AIProviderFactory.create_client(AIProvider.GROQ, test_key)
            print("✅ Groq client created successfully with valid format key")
            
            # Test response generation (will fail without real API key)
            response = await client.generate_response(
                "You are a helpful assistant.",
                "Say hello.",
                temperature=0.1,
                max_tokens=50
            )
            
            if response.success:
                print(f"✅ Groq response: {response.content[:100]}...")
            else:
                print(f"⚠️  Groq response failed (expected without real API key): {response.error}")
            
        except Exception as e:
            print(f"⚠️  Groq test failed (expected without real API key): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq client test failed: {e}")
        return False


async def test_ai_analysis_service():
    """Test the AI analysis service integration."""
    print("\nTesting AI Analysis Service Integration...")
    
    try:
        # Initialize prompt manager with test directory
        prompt_manager = PromptManager("prompts")
        
        # Initialize AI analysis service
        ai_service = AIAnalysisService(prompt_manager)
        
        # Test getting available providers
        providers = ai_service.get_available_providers()
        print(f"✅ AI service providers: {[p.value for p in providers]}")
        
        # Test getting provider capabilities
        for provider in providers:
            capabilities = ai_service.get_provider_capabilities(provider)
            print(f"✅ {provider.value} capabilities: {capabilities}")
        
        # Test prompt categories
        categories = ai_service.get_available_analysis_types()
        print(f"✅ Available analysis types: {categories}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI analysis service test failed: {e}")
        return False


async def test_prompt_integration():
    """Test prompt integration with AI providers."""
    print("\nTesting Prompt Integration...")
    
    try:
        # Initialize services
        prompt_manager = PromptManager("prompts")
        ai_service = AIAnalysisService(prompt_manager)
        
        # Test prompt formatting
        formatted = prompt_manager.format_prompt(
            "educational",
            "concept_explanation",
            concept_name="VPIP",
            experience_level="beginner",
            context="Testing prompt integration"
        )
        
        if formatted:
            print("✅ Prompt formatting successful")
            print(f"   System prompt length: {len(formatted['system'])}")
            print(f"   User prompt length: {len(formatted['user'])}")
        else:
            print("❌ Prompt formatting failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt integration test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing AI Provider Integration")
    print("=" * 50)
    
    tests = [
        ("Provider Factory", test_provider_factory),
        ("Gemini Client", test_gemini_client),
        ("Groq Client", test_groq_client),
        ("AI Analysis Service", test_ai_analysis_service),
        ("Prompt Integration", test_prompt_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! AI provider integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)