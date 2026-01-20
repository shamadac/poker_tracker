"""
AI Provider Clients

This module implements clients for different AI providers (Gemini, Groq)
with a unified interface for poker analysis.

Requirements: 1.2, 1.4
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import httpx
import google.generativeai as genai
from groq import AsyncGroq

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI providers."""
    GEMINI = "gemini"
    GROQ = "groq"


@dataclass
class AIResponse:
    """Response from AI provider."""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[AIProvider] = None
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAIClient(ABC):
    """Base class for AI provider clients."""
    
    def __init__(self, api_key: str):
        """Initialize the AI client with API key."""
        self.api_key = api_key
        self._validate_api_key()
    
    @abstractmethod
    def _validate_api_key(self) -> None:
        """Validate the API key format."""
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> AIResponse:
        """Generate response from the AI provider."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> AIProvider:
        """Get the provider name."""
        pass


class GeminiClient(BaseAIClient):
    """Google Gemini AI client."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Google AI API key
            model: Gemini model to use (default: gemini-pro)
        """
        self.model_name = model
        super().__init__(api_key)
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def _validate_api_key(self) -> None:
        """Validate Gemini API key format."""
        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError("Gemini API key must be a non-empty string")
        
        # Basic format validation for Google API keys
        if len(self.api_key) < 20:
            raise ValueError("Gemini API key appears to be too short")
    
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> AIResponse:
        """
        Generate response using Gemini.
        
        Args:
            system_prompt: System instruction for the AI
            user_prompt: User's prompt/question
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            AIResponse with the generated content
        """
        try:
            # Combine system and user prompts for Gemini
            # Gemini doesn't have separate system/user roles like ChatGPT
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Extract generation parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                candidate_count=1,
            )
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                combined_prompt,
                generation_config=generation_config
            )
            
            if not response or not response.text:
                return AIResponse(
                    success=False,
                    error="Empty response from Gemini",
                    provider=AIProvider.GEMINI
                )
            
            # Extract usage information if available
            usage_info = {}
            if hasattr(response, 'usage_metadata'):
                usage_info = {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                    'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            return AIResponse(
                success=True,
                content=response.text,
                provider=AIProvider.GEMINI,
                usage=usage_info,
                metadata={
                    'model': self.model_name,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return AIResponse(
                success=False,
                error=f"Gemini API error: {str(e)}",
                provider=AIProvider.GEMINI
            )
    
    def get_provider_name(self) -> AIProvider:
        """Get the provider name."""
        return AIProvider.GEMINI


class GroqClient(BaseAIClient):
    """Groq AI client."""
    
    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key
            model: Groq model to use (default: mixtral-8x7b-32768)
        """
        self.model_name = model
        super().__init__(api_key)
        
        # Initialize Groq client
        self.client = AsyncGroq(api_key=self.api_key)
    
    def _validate_api_key(self) -> None:
        """Validate Groq API key format."""
        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError("Groq API key must be a non-empty string")
        
        # Basic format validation for Groq API keys
        if not self.api_key.startswith('gsk_'):
            raise ValueError("Groq API key should start with 'gsk_'")
        
        if len(self.api_key) < 40:
            raise ValueError("Groq API key appears to be too short")
    
    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> AIResponse:
        """
        Generate response using Groq.
        
        Args:
            system_prompt: System instruction for the AI
            user_prompt: User's prompt/question
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            AIResponse with the generated content
        """
        try:
            # Extract generation parameters
            temperature = kwargs.get('temperature', 0.7)
            max_tokens = kwargs.get('max_tokens', 2048)
            
            # Prepare messages for Groq (supports system/user roles)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            if not response or not response.choices:
                return AIResponse(
                    success=False,
                    error="Empty response from Groq",
                    provider=AIProvider.GROQ
                )
            
            content = response.choices[0].message.content
            if not content:
                return AIResponse(
                    success=False,
                    error="Empty content in Groq response",
                    provider=AIProvider.GROQ
                )
            
            # Extract usage information
            usage_info = {}
            if hasattr(response, 'usage') and response.usage:
                usage_info = {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            
            return AIResponse(
                success=True,
                content=content,
                provider=AIProvider.GROQ,
                usage=usage_info,
                metadata={
                    'model': self.model_name,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'finish_reason': response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating Groq response: {e}")
            return AIResponse(
                success=False,
                error=f"Groq API error: {str(e)}",
                provider=AIProvider.GROQ
            )
    
    def get_provider_name(self) -> AIProvider:
        """Get the provider name."""
        return AIProvider.GROQ


class AIProviderFactory:
    """Factory for creating AI provider clients."""
    
    @staticmethod
    def create_client(provider: AIProvider, api_key: str, **kwargs) -> BaseAIClient:
        """
        Create an AI client for the specified provider.
        
        Args:
            provider: AI provider to use
            api_key: API key for the provider
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured AI client instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider == AIProvider.GEMINI:
            model = kwargs.get('model', 'gemini-1.5-pro-latest')
            return GeminiClient(api_key, model)
        elif provider == AIProvider.GROQ:
            model = kwargs.get('model', 'llama3-8b-8192')
            return GroqClient(api_key, model)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    @staticmethod
    def get_available_providers() -> list[AIProvider]:
        """Get list of available AI providers."""
        return [AIProvider.GEMINI, AIProvider.GROQ]
    
    @staticmethod
    def get_default_models() -> Dict[AIProvider, str]:
        """Get default models for each provider."""
        return {
            AIProvider.GEMINI: "gemini-1.5-pro-latest",
            AIProvider.GROQ: "llama3-8b-8192"
        }
    
    @staticmethod
    async def validate_api_key(provider: AIProvider, api_key: str) -> bool:
        """
        Validate an API key by making a test request.
        
        Args:
            provider: AI provider to test
            api_key: API key to validate
            
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            client = AIProviderFactory.create_client(provider, api_key)
            
            # Make a simple test request
            test_response = await client.generate_response(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'API key is valid' if you can read this.",
                temperature=0.1,
                max_tokens=50
            )
            
            return test_response.success and test_response.content is not None
            
        except Exception as e:
            logger.error(f"API key validation failed for {provider}: {e}")
            return False


# Provider-specific model options
GEMINI_MODELS = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro"
]

GROQ_MODELS = [
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]

# Provider capabilities
PROVIDER_CAPABILITIES = {
    AIProvider.GEMINI: {
        "max_tokens": 8192,
        "supports_system_prompt": False,  # Uses combined prompts
        "supports_streaming": False,
        "supports_vision": True,  # With gemini-pro-vision
        "rate_limits": {
            "requests_per_minute": 60,
            "tokens_per_minute": 32000
        }
    },
    AIProvider.GROQ: {
        "max_tokens": 32768,
        "supports_system_prompt": True,
        "supports_streaming": True,
        "supports_vision": False,
        "rate_limits": {
            "requests_per_minute": 30,
            "tokens_per_minute": 6000
        }
    }
}