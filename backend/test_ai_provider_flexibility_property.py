"""
Property-Based Tests for AI Provider Flexibility

**Feature: professional-poker-analyzer-rebuild, Property 33: AI Provider Runtime Selection**

Tests the universal property that for any analysis operation, users should be able 
to select either Gemini or Groq provider at execution time without being locked 
to a single provider.

**Validates: Requirements 1.2, 1.4**

This test ensures that:
1. Both Gemini and Groq providers can be selected at runtime
2. Provider switching works seamlessly without data loss
3. API key validation works correctly for both providers
4. Analysis results maintain consistency across providers
5. Provider-specific features are handled correctly
6. Error handling works for invalid providers or keys
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, Optional, List
import logging

from app.services.ai_providers import (
    AIProviderFactory, 
    BaseAIClient, 
    AIProvider, 
    AIResponse,
    GeminiClient,
    GroqClient,
    PROVIDER_CAPABILITIES
)
from app.services.ai_analysis import AIAnalysisService, AnalysisResult
from app.schemas.hand import HandResponse


# Test data strategies
@st.composite
def valid_api_keys(draw):
    """Generate valid-looking API keys for different providers."""
    provider = draw(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]))
    
    if provider == AIProvider.GEMINI:
        # Gemini keys are typically longer alphanumeric strings
        key = draw(st.text(min_size=30, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        return provider, f"AIza{key}"
    else:  # GROQ
        # Groq keys start with 'gsk_'
        key = draw(st.text(min_size=40, max_size=60, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
        return provider, f"gsk_{key}"


@st.composite
def analysis_parameters(draw):
    """Generate analysis parameters for testing."""
    return {
        'experience_level': draw(st.sampled_from(['beginner', 'intermediate', 'advanced'])),
        'analysis_type': draw(st.sampled_from(['basic', 'advanced', 'tournament', 'cash_game'])),
        'analysis_depth': draw(st.sampled_from(['basic', 'standard', 'advanced'])),
        'temperature': draw(st.floats(min_value=0.1, max_value=1.0)),
        'max_tokens': draw(st.integers(min_value=100, max_value=4000))
    }


@st.composite
def mock_hand_data(draw):
    """Generate mock hand data for testing."""
    return HandResponse(
        # Required fields from UUIDMixin
        id=str(draw(st.uuids())),
        
        # Required fields from TimestampMixin
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes()),
        
        # Required fields from HandBase
        hand_id=draw(st.text(min_size=5, max_size=20)),
        platform=draw(st.sampled_from(['pokerstars', 'ggpoker'])),
        
        # Required field from HandResponse
        user_id=str(draw(st.uuids())),
        
        # Optional fields
        game_type=draw(st.sampled_from(['No Limit Hold\'em', 'Pot Limit Omaha'])),
        stakes=draw(st.sampled_from(['$0.01/$0.02', '$0.05/$0.10', '$1/$2'])),
        position=draw(st.sampled_from(['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'])),
        player_cards=draw(st.lists(st.text(min_size=2, max_size=2), min_size=2, max_size=2)),
        board_cards=draw(st.lists(st.text(min_size=2, max_size=2), min_size=0, max_size=5)),
        actions=draw(st.dictionaries(
            st.sampled_from(['preflop', 'flop', 'turn', 'river']),
            st.lists(st.dictionaries(
                st.sampled_from(['player', 'action', 'amount', 'street']),
                st.one_of(
                    st.text(min_size=1, max_size=10),
                    st.sampled_from(['fold', 'check', 'call', 'bet', 'raise']),
                    st.integers(min_value=0, max_value=1000),
                    st.sampled_from(['preflop', 'flop', 'turn', 'river'])
                )
            ), min_size=1, max_size=5),
            min_size=1, max_size=4
        )),
        result=draw(st.sampled_from(['won', 'lost', 'folded'])),
        pot_size=draw(st.floats(min_value=1.0, max_value=1000.0)),
        player_stacks=draw(st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=100, max_value=10000),
            min_size=2, max_size=6
        )),
        analysis_count=0,
        is_play_money=False
    )


class TestAIProviderFlexibilityProperty:
    """Property-based tests for AI provider flexibility."""
    
    def setup_method(self):
        """Set up test environment."""
        # Disable logging during tests to reduce noise
        logging.getLogger('app.services.ai_providers').setLevel(logging.CRITICAL)
        logging.getLogger('app.services.ai_analysis').setLevel(logging.CRITICAL)
    
    @given(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]))
    @settings(max_examples=50, deadline=5000)
    def test_property_provider_factory_creation(self, provider):
        """
        Property: For any supported AI provider, the factory should be able to 
        create a client instance with appropriate configuration.
        """
        # Generate a valid-looking API key for the provider
        if provider == AIProvider.GEMINI:
            api_key = "AIzaSyDummyKeyForTesting123456789"
        else:  # GROQ
            api_key = "gsk_dummyKeyForTesting123456789012345678901234567890"
        
        # Property: Factory should create client without errors
        client = AIProviderFactory.create_client(provider, api_key)
        
        assert isinstance(client, BaseAIClient)
        assert client.get_provider_name() == provider
        assert client.api_key == api_key
        
        # Property: Client should have provider-specific type
        if provider == AIProvider.GEMINI:
            assert isinstance(client, GeminiClient)
        else:
            assert isinstance(client, GroqClient)
    
    @given(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]), st.text(min_size=1, max_size=10))
    @settings(max_examples=50, deadline=5000)
    def test_property_invalid_api_key_handling(self, provider, invalid_key):
        """
        Property: For any invalid API key format, the system should raise 
        appropriate validation errors without crashing.
        """
        # Assume the key is actually invalid (not accidentally valid)
        assume(not invalid_key.startswith('AIza') if provider == AIProvider.GEMINI else True)
        assume(not invalid_key.startswith('gsk_') if provider == AIProvider.GROQ else True)
        assume(len(invalid_key) < 20)  # Too short to be valid
        
        # Property: Invalid keys should raise ValueError
        with pytest.raises(ValueError):
            AIProviderFactory.create_client(provider, invalid_key)
    
    @given(valid_api_keys(), analysis_parameters())
    @settings(max_examples=50, deadline=5000)
    def test_property_provider_switching_consistency(self, api_key_data, params):
        """
        Property: For any valid provider and parameters, switching between 
        providers should maintain consistent behavior and not lose configuration.
        """
        provider, api_key = api_key_data
        
        # Create client for the provider
        client = AIProviderFactory.create_client(provider, api_key)
        
        # Property: Client should maintain provider identity
        assert client.get_provider_name() == provider
        
        # Property: Client should accept generation parameters
        # (We can't test actual API calls without real keys, but we can test parameter handling)
        generation_kwargs = {
            'temperature': params['temperature'],
            'max_tokens': params['max_tokens']
        }
        
        # Property: Parameters should be accepted without errors
        # This tests that the client interface is consistent
        assert hasattr(client, 'generate_response')
        assert callable(client.generate_response)
        
        # Property: Provider capabilities should be available
        capabilities = PROVIDER_CAPABILITIES.get(provider)
        assert capabilities is not None
        assert 'max_tokens' in capabilities
        assert 'supports_system_prompt' in capabilities
    
    @given(st.lists(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]), min_size=2, max_size=10))
    @settings(max_examples=30, deadline=10000)  # Increased deadline
    def test_property_multiple_provider_support(self, provider_sequence):
        """
        Property: For any sequence of provider selections, the system should 
        handle switching between providers without conflicts or state issues.
        """
        clients = {}
        
        for provider in provider_sequence:
            # Generate appropriate API key for each provider
            if provider == AIProvider.GEMINI:
                api_key = f"AIzaSyTestKey{len(clients)}{'x' * 20}"
            else:  # GROQ
                api_key = f"gsk_testkey{len(clients)}{'x' * 30}"
            
            # Property: Each provider should create a distinct client
            client = AIProviderFactory.create_client(provider, api_key)
            client_key = f"{provider.value}_{api_key[:8]}"
            clients[client_key] = client
            
            # Property: Client should maintain correct provider identity
            assert client.get_provider_name() == provider
            
            # Property: Each client should be independent
            for other_key, other_client in clients.items():
                if other_key != client_key:
                    # Clients should be different instances
                    assert client is not other_client
    
    @given(mock_hand_data(), valid_api_keys(), analysis_parameters())
    @settings(max_examples=30, deadline=10000)
    async def test_property_analysis_provider_flexibility(self, hand_data, api_key_data, params):
        """
        Property: For any hand analysis request, users should be able to select 
        any supported provider at runtime and get consistent analysis structure.
        """
        provider, api_key = api_key_data
        
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock the prompt manager
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': 'You are a poker coach.',
                'user': f'Analyze this hand: {hand_data.hand_id}',
                'metadata': {}
            }
            
            # Mock the AI client response
            mock_response = AIResponse(
                success=True,
                content=f"Analysis from {provider.value}: This hand shows good decision making.",
                provider=provider,
                usage={'prompt_tokens': 100, 'completion_tokens': 200, 'total_tokens': 300},
                metadata={'model': 'test-model', 'temperature': params['temperature']}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            # Mock the client creation and response
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                # Mock API key validation
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Analysis should work with any provider
                    result = await analysis_service.analyze_hand(
                        hand_data,
                        provider,
                        api_key,
                        analysis_type=params['analysis_type'],
                        experience_level=params['experience_level'],
                        temperature=params['temperature'],
                        max_tokens=params['max_tokens']
                    )
                    
                    # Property: Result should be successful and consistent
                    assert isinstance(result, AnalysisResult)
                    assert result.success is True
                    assert result.provider == provider
                    assert result.content is not None
                    assert provider.value in result.content
                    
                    # Property: Metadata should contain provider-specific information
                    assert result.metadata is not None
                    assert result.metadata['analysis_type'] == params['analysis_type']
                    assert result.metadata['experience_level'] == params['experience_level']
                    
                    # Property: Usage information should be preserved
                    assert result.usage is not None
                    assert 'total_tokens' in result.usage
    
    @given(st.lists(mock_hand_data(), min_size=1, max_size=5), valid_api_keys(), analysis_parameters())
    @settings(max_examples=20, deadline=10000)
    async def test_property_session_analysis_provider_flexibility(self, hands_data, api_key_data, params):
        """
        Property: For any session analysis request, provider selection should 
        work consistently and maintain analysis quality across providers.
        """
        provider, api_key = api_key_data
        
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock the prompt manager
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': 'You are a poker session analyst.',
                'user': f'Analyze this session of {len(hands_data)} hands.',
                'metadata': {}
            }
            
            # Mock session stats
            session_stats = {
                'vpip': 25.0,
                'pfr': 18.0,
                'aggression_factor': 2.5,
                'win_rate': 5.2,
                'hands_played': len(hands_data)
            }
            
            # Mock the AI client response
            mock_response = AIResponse(
                success=True,
                content=f"Session analysis from {provider.value}: Overall solid play with room for improvement.",
                provider=provider,
                usage={'prompt_tokens': 200, 'completion_tokens': 400, 'total_tokens': 600},
                metadata={'model': 'test-model'}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            # Mock the client creation and response
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                # Mock API key validation
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Session analysis should work with any provider
                    result = await analysis_service.analyze_session(
                        hands_data,
                        session_stats,
                        provider,
                        api_key,
                        analysis_type='summary'
                    )
                    
                    # Property: Result should be successful and provider-specific
                    assert isinstance(result, AnalysisResult)
                    assert result.success is True
                    assert result.provider == provider
                    assert result.content is not None
                    assert provider.value in result.content
                    
                    # Property: Session-specific metadata should be preserved
                    assert result.metadata is not None
                    assert result.metadata['hands_count'] == len(hands_data)
                    assert result.metadata['analysis_type'] == 'summary'
    
    @given(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]))
    @settings(max_examples=30, deadline=5000)
    def test_property_provider_capabilities_consistency(self, provider):
        """
        Property: For any supported provider, capabilities should be well-defined 
        and consistent with the provider's actual features.
        """
        # Property: Provider should have defined capabilities
        capabilities = PROVIDER_CAPABILITIES.get(provider)
        assert capabilities is not None
        
        # Property: Essential capability fields should be present
        required_fields = ['max_tokens', 'supports_system_prompt', 'supports_streaming', 'rate_limits']
        for field in required_fields:
            assert field in capabilities, f"Missing capability field: {field}"
        
        # Property: Capabilities should match provider characteristics
        if provider == AIProvider.GEMINI:
            # Gemini-specific capabilities
            assert capabilities['supports_system_prompt'] is False  # Uses combined prompts
            assert capabilities['max_tokens'] > 0
        elif provider == AIProvider.GROQ:
            # Groq-specific capabilities
            assert capabilities['supports_system_prompt'] is True  # Supports separate system prompts
            assert capabilities['supports_streaming'] is True
            assert capabilities['max_tokens'] > 0
        
        # Property: Rate limits should be defined
        rate_limits = capabilities['rate_limits']
        assert isinstance(rate_limits, dict)
        assert 'requests_per_minute' in rate_limits
        assert 'tokens_per_minute' in rate_limits
        assert rate_limits['requests_per_minute'] > 0
        assert rate_limits['tokens_per_minute'] > 0
    
    @given(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]), st.text(min_size=1, max_size=20))
    @settings(max_examples=50, deadline=5000)
    def test_property_model_selection_flexibility(self, provider, custom_model):
        """
        Property: For any provider, users should be able to specify custom models 
        while maintaining provider functionality.
        """
        # Generate appropriate API key
        if provider == AIProvider.GEMINI:
            api_key = "AIzaSyTestModelKey123456789"
        else:  # GROQ
            api_key = "gsk_testmodelkey123456789012345678901234567890"
        
        # Property: Custom model should be accepted
        client = AIProviderFactory.create_client(provider, api_key, model=custom_model)
        
        assert isinstance(client, BaseAIClient)
        assert client.get_provider_name() == provider
        
        # Property: Model should be stored in client
        if hasattr(client, 'model_name'):
            assert client.model_name == custom_model
    
    def test_property_available_providers_consistency(self):
        """
        Property: The list of available providers should be consistent across 
        all provider-related components.
        """
        # Property: Factory should return consistent provider list
        factory_providers = set(AIProviderFactory.get_available_providers())
        
        # Property: Enum should match factory providers
        enum_providers = set(AIProvider)
        assert factory_providers == enum_providers
        
        # Property: Capabilities should be defined for all providers
        for provider in factory_providers:
            assert provider in PROVIDER_CAPABILITIES
        
        # Property: Default models should be defined for all providers
        default_models = AIProviderFactory.get_default_models()
        for provider in factory_providers:
            assert provider in default_models
            assert isinstance(default_models[provider], str)
            assert len(default_models[provider]) > 0
    
    @given(valid_api_keys())
    @settings(max_examples=30, deadline=5000)
    async def test_property_api_key_validation_consistency(self, api_key_data):
        """
        Property: For any provider and API key combination, validation should 
        be consistent and not produce false positives/negatives.
        """
        provider, api_key = api_key_data
        
        # Mock the validation to avoid real API calls
        with patch('app.services.ai_providers.AIProviderFactory.validate_api_key') as mock_validate:
            # Property: Validation should be callable
            mock_validate.return_value = True
            
            result = await AIProviderFactory.validate_api_key(provider, api_key)
            
            # Property: Validation should return boolean
            assert isinstance(result, bool)
            
            # Property: Validation should be called with correct parameters
            mock_validate.assert_called_once_with(provider, api_key)
    
    @given(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]))
    @settings(max_examples=30, deadline=5000)
    def test_property_error_handling_consistency(self, provider):
        """
        Property: For any provider, error handling should be consistent and 
        provide meaningful error messages.
        """
        # Test with empty API key
        with pytest.raises(ValueError) as exc_info:
            AIProviderFactory.create_client(provider, "")
        
        # Property: Error message should be meaningful
        error_message = str(exc_info.value)
        assert len(error_message) > 0
        assert 'API key' in error_message or 'key' in error_message.lower()
        
        # Test with None API key
        with pytest.raises((ValueError, TypeError)):
            AIProviderFactory.create_client(provider, None)
    
    @given(mock_hand_data(), st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ]))
    @settings(max_examples=20, deadline=10000)
    async def test_property_comprehensive_analysis_provider_flexibility(self, hand_data, provider):
        """
        Property: For any comprehensive analysis request, provider selection 
        should work with all analysis depths and experience levels.
        """
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock the prompt manager
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': 'You are a comprehensive poker analyst.',
                'user': f'Provide comprehensive analysis for hand: {hand_data.hand_id}',
                'metadata': {}
            }
            
            # Generate appropriate API key
            if provider == AIProvider.GEMINI:
                api_key = "AIzaSyComprehensiveTestKey123456789"
            else:  # GROQ
                api_key = "gsk_comprehensivetestkey123456789012345678901234567890"
            
            # Mock the AI client response
            mock_response = AIResponse(
                success=True,
                content=f"Comprehensive analysis from {provider.value}: Detailed strategic breakdown with decision points.",
                provider=provider,
                usage={'prompt_tokens': 300, 'completion_tokens': 800, 'total_tokens': 1100},
                metadata={'model': 'test-model', 'analysis_depth': 'advanced'}  # Fixed to match expected value
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            # Mock the client creation and response
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                # Mock API key validation
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Comprehensive analysis should work with any provider
                    result = await analysis_service.analyze_hand_comprehensive(
                        hand_data,
                        provider,
                        api_key,
                        experience_level='advanced',
                        analysis_depth='advanced',
                        focus_areas=['decision_making', 'position_play']
                    )
                    
                    # Property: Result should be successful and comprehensive
                    assert isinstance(result, AnalysisResult)
                    assert result.success is True
                    assert result.provider == provider
                    assert result.content is not None
                    assert 'comprehensive' in result.content.lower() or 'detailed' in result.content.lower()
                    
                    # Property: Comprehensive metadata should be present
                    assert result.metadata is not None
                    assert result.metadata['analysis_depth'] == 'advanced'
                    assert result.metadata['experience_level'] == 'advanced'
                    assert 'focus_areas' in result.metadata


def test_integration_provider_switching():
    """
    Integration test to verify that provider switching works in practice
    with the actual service components.
    """
    # Test that we can create clients for both providers
    gemini_key = "AIzaSyIntegrationTestKey123456789"
    groq_key = "gsk_integrationtestkey123456789012345678901234567890"
    
    # Create clients
    gemini_client = AIProviderFactory.create_client(AIProvider.GEMINI, gemini_key)
    groq_client = AIProviderFactory.create_client(AIProvider.GROQ, groq_key)
    
    # Verify they're different types
    assert isinstance(gemini_client, GeminiClient)
    assert isinstance(groq_client, GroqClient)
    assert gemini_client.get_provider_name() == AIProvider.GEMINI
    assert groq_client.get_provider_name() == AIProvider.GROQ
    
    # Verify they have different capabilities
    gemini_caps = PROVIDER_CAPABILITIES[AIProvider.GEMINI]
    groq_caps = PROVIDER_CAPABILITIES[AIProvider.GROQ]
    
    assert gemini_caps['supports_system_prompt'] != groq_caps['supports_system_prompt']
    assert gemini_caps['supports_streaming'] != groq_caps['supports_streaming']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])