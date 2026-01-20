"""
AI Analysis Service with YAML Prompt Integration

This service provides AI-powered poker analysis using configurable YAML prompts
and multiple AI providers (Gemini, Groq).

Requirements: 7.1, 7.2, 1.2, 1.4
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import asyncio
import json

from .prompt_manager import get_prompt_manager, PromptManager
from .ai_providers import (
    AIProviderFactory, 
    BaseAIClient, 
    AIProvider, 
    AIResponse,
    PROVIDER_CAPABILITIES
)
from ..schemas.hand import HandResponse, DetailedAction
from ..schemas.analysis import AnalysisResponse, SessionAnalysisResponse
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRequest:
    """Request for AI analysis."""
    provider: AIProvider
    api_key: str
    prompt_category: str
    prompt_type: str
    data: Dict[str, Any]
    user_id: str
    experience_level: str = "intermediate"


@dataclass
class AnalysisResult:
    """Result from AI analysis."""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    provider: Optional[AIProvider] = None
    prompt_used: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None


class AIAnalysisService:
    """
    Service for AI-powered poker analysis using YAML prompts.
    
    Provides functionality to:
    - Analyze individual hands with strategic advice
    - Generate session analysis and patterns
    - Provide educational content and explanations
    - Support multiple AI providers with runtime selection
    """
    
    def __init__(self, prompt_manager: Optional[PromptManager] = None):
        """
        Initialize the AI analysis service.
        
        Args:
            prompt_manager: Optional prompt manager instance
        """
        self.prompt_manager = prompt_manager or get_prompt_manager()
        self._client_cache: Dict[str, BaseAIClient] = {}
    
    def _get_api_key(self, provider: AIProvider, user_api_key: Optional[str] = None) -> str:
        """
        Get the appropriate API key for the provider.
        
        Priority:
        1. User-provided API key (for production)
        2. Development API key (for local development)
        3. Empty string (will cause validation to fail)
        
        Args:
            provider: AI provider
            user_api_key: User-provided API key
            
        Returns:
            API key to use
        """
        # If user provided an API key, use it
        if user_api_key and user_api_key.strip():
            return user_api_key.strip()
        
        # If in development mode, use development API keys
        if settings.USE_DEV_API_KEYS:
            dev_key = settings.get_dev_api_key(provider.value)
            if dev_key:
                logger.info(f"Using development API key for {provider.value}")
                return dev_key
        
        # No API key available
        return ""
    
    def _get_client_cache_key(self, provider: AIProvider, api_key: str, model: Optional[str] = None) -> str:
        """Generate cache key for AI client."""
        # Use first 8 chars of API key for caching (security)
        key_prefix = api_key[:8] if len(api_key) >= 8 else api_key
        model_suffix = f"_{model}" if model else ""
        return f"{provider.value}_{key_prefix}{model_suffix}"
    
    def _get_or_create_client(
        self, 
        provider: AIProvider, 
        api_key: str, 
        model: Optional[str] = None
    ) -> BaseAIClient:
        """Get cached client or create new one."""
        cache_key = self._get_client_cache_key(provider, api_key, model)
        
        if cache_key not in self._client_cache:
            kwargs = {}
            if model:
                kwargs['model'] = model
            
            self._client_cache[cache_key] = AIProviderFactory.create_client(
                provider, api_key, **kwargs
            )
        
        return self._client_cache[cache_key]
    
    async def analyze_hand_comprehensive(
        self,
        hand: HandResponse,
        provider: AIProvider,
        api_key: str,
        experience_level: str = "intermediate",
        analysis_depth: str = "standard",
        focus_areas: Optional[List[str]] = None,
        model: Optional[str] = None,
        **generation_kwargs
    ) -> AnalysisResult:
        """
        Comprehensive hand-by-hand analysis with adaptive depth.
        
        Implements requirements 7.1, 7.6, 7.8:
        - Strategic advice for each decision point (7.1)
        - Hand-by-hand breakdowns with specific recommendations (7.6)
        - Adaptive analysis depth based on user experience level (7.8)
        
        Args:
            hand: Poker hand to analyze
            provider: AI provider to use
            api_key: API key for the provider (or empty for dev keys)
            experience_level: Player's experience level (beginner, intermediate, advanced)
            analysis_depth: Analysis depth (basic, standard, advanced)
            focus_areas: Specific areas to focus on
            model: Optional specific model to use
            **generation_kwargs: Additional parameters for AI generation
            
        Returns:
            AnalysisResult with comprehensive analysis content
        """
        try:
            # Get the appropriate API key (user-provided or development)
            resolved_api_key = self._get_api_key(provider, api_key)
            
            # Validate API key
            if not await self.validate_api_key(provider, resolved_api_key):
                return AnalysisResult(
                    success=False,
                    error="Invalid API key for the selected provider",
                    provider=provider
                )
            
            # Determine analysis type based on experience level and depth
            analysis_type = self._determine_analysis_type(experience_level, analysis_depth)
            
            # Prepare comprehensive hand data for prompt formatting
            hand_data = self._prepare_comprehensive_hand_data(hand, experience_level, focus_areas)
            
            # Get formatted prompt for comprehensive analysis
            formatted_prompt = self.prompt_manager.format_prompt(
                "hand_analysis",
                analysis_type,
                **hand_data
            )
            
            if not formatted_prompt:
                return AnalysisResult(
                    success=False,
                    error=f"Failed to get prompt for hand_analysis.{analysis_type}",
                    provider=provider
                )
            
            # Get AI client and call provider
            client = self._get_or_create_client(provider, resolved_api_key, model)
            ai_response = await client.generate_response(
                formatted_prompt['system'],
                formatted_prompt['user'],
                **generation_kwargs
            )
            
            if not ai_response.success:
                return AnalysisResult(
                    success=False,
                    error=ai_response.error or "Failed to get response from AI provider",
                    provider=provider
                )
            
            # Post-process the analysis to extract structured insights
            structured_analysis = self._extract_structured_insights(ai_response.content, analysis_type)
            
            return AnalysisResult(
                success=True,
                content=ai_response.content,
                provider=provider,
                prompt_used=formatted_prompt,
                usage=ai_response.usage,
                metadata={
                    'analysis_type': analysis_type,
                    'experience_level': experience_level,
                    'analysis_depth': analysis_depth,
                    'focus_areas': focus_areas or [],
                    'hand_id': hand.hand_id,
                    'model': model or "default",
                    'structured_insights': structured_analysis,
                    'used_dev_key': settings.USE_DEV_API_KEYS and not api_key,
                    **ai_response.metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive hand analysis {hand.hand_id}: {e}")
            return AnalysisResult(
                success=False,
                error=f"Comprehensive analysis failed: {str(e)}",
                provider=provider
            )

    async def analyze_hand(
        self,
        hand: HandResponse,
        provider: AIProvider,
        api_key: str,
        analysis_type: str = "basic",
        experience_level: str = "intermediate",
        model: Optional[str] = None,
        **generation_kwargs
    ) -> AnalysisResult:
        """
        Analyze a single poker hand using AI.
        
        Args:
            hand: Poker hand to analyze
            provider: AI provider to use
            api_key: API key for the provider
            analysis_type: Type of analysis (basic, advanced, tournament, etc.)
            experience_level: Player's experience level
            model: Optional specific model to use
            **generation_kwargs: Additional parameters for AI generation
            
        Returns:
            AnalysisResult with the analysis content
        """
        try:
            # Validate API key first
            if not await self.validate_api_key(provider, api_key):
                return AnalysisResult(
                    success=False,
                    error="Invalid API key for the selected provider",
                    provider=provider
                )
            
            # Prepare hand data for prompt formatting
            hand_data = self._prepare_hand_data(hand, experience_level)
            
            # Get formatted prompt
            formatted_prompt = self.prompt_manager.format_prompt(
                "hand_analysis",
                analysis_type,
                **hand_data
            )
            
            if not formatted_prompt:
                return AnalysisResult(
                    success=False,
                    error=f"Failed to get prompt for hand_analysis.{analysis_type}",
                    provider=provider
                )
            
            # Get AI client and call provider
            client = self._get_or_create_client(provider, api_key, model)
            ai_response = await client.generate_response(
                formatted_prompt['system'],
                formatted_prompt['user'],
                **generation_kwargs
            )
            
            if not ai_response.success:
                return AnalysisResult(
                    success=False,
                    error=ai_response.error or "Failed to get response from AI provider",
                    provider=provider
                )
            
            return AnalysisResult(
                success=True,
                content=ai_response.content,
                provider=provider,
                prompt_used=formatted_prompt,
                usage=ai_response.usage,
                metadata={
                    'analysis_type': analysis_type,
                    'experience_level': experience_level,
                    'hand_id': hand.hand_id,
                    'model': model or "default",
                    **ai_response.metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing hand {hand.hand_id}: {e}")
            return AnalysisResult(
                success=False,
                error=f"Analysis failed: {str(e)}",
                provider=provider
            )
    
    async def analyze_session_comprehensive(
        self,
        hands: List[HandResponse],
        session_stats: Dict[str, Any],
        provider: AIProvider,
        api_key: str,
        analysis_type: str = "summary",
        experience_level: str = "intermediate",
        include_individual_hands: bool = True,
        model: Optional[str] = None,
        **generation_kwargs
    ) -> AnalysisResult:
        """
        Comprehensive session analysis with individual hand breakdowns.
        
        Implements requirements 7.1, 7.6, 7.8:
        - Strategic advice for session patterns and individual decisions (7.1)
        - Session-level breakdowns with specific recommendations (7.6)
        - Adaptive analysis depth based on user experience level (7.8)
        
        Args:
            hands: List of poker hands from the session
            session_stats: Calculated session statistics
            provider: AI provider to use
            api_key: API key for the provider (or empty for dev keys)
            analysis_type: Type of session analysis
            experience_level: Player's experience level
            include_individual_hands: Whether to include individual hand analysis
            model: Optional specific model to use
            **generation_kwargs: Additional parameters for AI generation
            
        Returns:
            AnalysisResult with comprehensive session analysis
        """
        try:
            # Get the appropriate API key (user-provided or development)
            resolved_api_key = self._get_api_key(provider, api_key)
            
            # Validate API key
            if not await self.validate_api_key(provider, resolved_api_key):
                return AnalysisResult(
                    success=False,
                    error="Invalid API key for the selected provider",
                    provider=provider
                )
            
            # Prepare comprehensive session data
            session_data = self._prepare_comprehensive_session_data(
                hands, session_stats, experience_level, include_individual_hands
            )
            
            # Determine analysis type based on experience level
            session_analysis_type = self._determine_session_analysis_type(experience_level, analysis_type)
            
            # Get formatted prompt
            formatted_prompt = self.prompt_manager.format_prompt(
                "session_analysis",
                session_analysis_type,
                **session_data
            )
            
            if not formatted_prompt:
                return AnalysisResult(
                    success=False,
                    error=f"Failed to get prompt for session_analysis.{session_analysis_type}",
                    provider=provider
                )
            
            # Get AI client and call provider
            client = self._get_or_create_client(provider, resolved_api_key, model)
            ai_response = await client.generate_response(
                formatted_prompt['system'],
                formatted_prompt['user'],
                **generation_kwargs
            )
            
            if not ai_response.success:
                return AnalysisResult(
                    success=False,
                    error=ai_response.error or "Failed to get response from AI provider",
                    provider=provider
                )
            
            # Extract structured session insights
            structured_insights = self._extract_session_insights(ai_response.content, session_analysis_type)
            
            return AnalysisResult(
                success=True,
                content=ai_response.content,
                provider=provider,
                prompt_used=formatted_prompt,
                usage=ai_response.usage,
                metadata={
                    'analysis_type': session_analysis_type,
                    'experience_level': experience_level,
                    'hands_count': len(hands),
                    'session_duration': session_data.get('time_duration', 'unknown'),
                    'include_individual_hands': include_individual_hands,
                    'model': model or "default",
                    'structured_insights': structured_insights,
                    'used_dev_key': settings.USE_DEV_API_KEYS and not api_key,
                    **ai_response.metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive session analysis: {e}")
            return AnalysisResult(
                success=False,
                error=f"Comprehensive session analysis failed: {str(e)}",
                provider=provider
            )

    async def analyze_session(
        self,
        hands: List[HandResponse],
        session_stats: Dict[str, Any],
        provider: AIProvider,
        api_key: str,
        analysis_type: str = "summary",
        model: Optional[str] = None,
        **generation_kwargs
    ) -> AnalysisResult:
        """
        Analyze a poker session with multiple hands.
        
        Args:
            hands: List of poker hands from the session
            session_stats: Calculated session statistics
            provider: AI provider to use
            api_key: API key for the provider
            analysis_type: Type of session analysis
            model: Optional specific model to use
            **generation_kwargs: Additional parameters for AI generation
            
        Returns:
            AnalysisResult with the session analysis
        """
        try:
            # Validate API key first
            if not await self.validate_api_key(provider, api_key):
                return AnalysisResult(
                    success=False,
                    error="Invalid API key for the selected provider",
                    provider=provider
                )
            
            # Prepare session data for prompt formatting
            session_data = self._prepare_session_data(hands, session_stats)
            
            # Get formatted prompt
            formatted_prompt = self.prompt_manager.format_prompt(
                "session_analysis",
                analysis_type,
                **session_data
            )
            
            if not formatted_prompt:
                return AnalysisResult(
                    success=False,
                    error=f"Failed to get prompt for session_analysis.{analysis_type}",
                    provider=provider
                )
            
            # Get AI client and call provider
            client = self._get_or_create_client(provider, api_key, model)
            ai_response = await client.generate_response(
                formatted_prompt['system'],
                formatted_prompt['user'],
                **generation_kwargs
            )
            
            if not ai_response.success:
                return AnalysisResult(
                    success=False,
                    error=ai_response.error or "Failed to get response from AI provider",
                    provider=provider
                )
            
            return AnalysisResult(
                success=True,
                content=ai_response.content,
                provider=provider,
                prompt_used=formatted_prompt,
                usage=ai_response.usage,
                metadata={
                    'analysis_type': analysis_type,
                    'hands_count': len(hands),
                    'session_duration': session_data.get('time_duration', 'unknown'),
                    'model': model or "default",
                    **ai_response.metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing session: {e}")
            return AnalysisResult(
                success=False,
                error=f"Session analysis failed: {str(e)}",
                provider=provider
            )
    
    async def get_educational_content(
        self,
        concept: str,
        provider: AIProvider,
        api_key: str,
        experience_level: str = "intermediate",
        context: Optional[str] = None,
        model: Optional[str] = None,
        **generation_kwargs
    ) -> AnalysisResult:
        """
        Get educational content about a poker concept.
        
        Args:
            concept: Poker concept to explain
            provider: AI provider to use
            api_key: API key for the provider
            experience_level: Student's experience level
            context: Optional context for the explanation
            model: Optional specific model to use
            **generation_kwargs: Additional parameters for AI generation
            
        Returns:
            AnalysisResult with educational content
        """
        try:
            # Validate API key first
            if not await self.validate_api_key(provider, api_key):
                return AnalysisResult(
                    success=False,
                    error="Invalid API key for the selected provider",
                    provider=provider
                )
            
            # Prepare educational data
            educational_data = {
                'concept_name': concept,
                'experience_level': experience_level,
                'context': context or "general poker education"
            }
            
            # Get formatted prompt
            formatted_prompt = self.prompt_manager.format_prompt(
                "educational",
                "concept_explanation",
                **educational_data
            )
            
            if not formatted_prompt:
                return AnalysisResult(
                    success=False,
                    error="Failed to get educational prompt",
                    provider=provider
                )
            
            # Get AI client and call provider
            client = self._get_or_create_client(provider, api_key, model)
            ai_response = await client.generate_response(
                formatted_prompt['system'],
                formatted_prompt['user'],
                **generation_kwargs
            )
            
            if not ai_response.success:
                return AnalysisResult(
                    success=False,
                    error=ai_response.error or "Failed to get educational content from AI provider",
                    provider=provider
                )
            
            return AnalysisResult(
                success=True,
                content=ai_response.content,
                provider=provider,
                prompt_used=formatted_prompt,
                usage=ai_response.usage,
                metadata={
                    'concept': concept,
                    'experience_level': experience_level,
                    'model': model or "default",
                    **ai_response.metadata
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting educational content for {concept}: {e}")
            return AnalysisResult(
                success=False,
                error=f"Educational content generation failed: {str(e)}",
                provider=provider
            )
    
    def _determine_analysis_type(self, experience_level: str, analysis_depth: str) -> str:
        """
        Determine the appropriate analysis type based on experience level and depth.
        
        Implements adaptive analysis depth (requirement 7.8).
        """
        # Map experience levels and depths to analysis types
        analysis_mapping = {
            ("beginner", "basic"): "basic",
            ("beginner", "standard"): "basic",
            ("beginner", "advanced"): "basic",  # Keep beginners on basic
            ("intermediate", "basic"): "basic",
            ("intermediate", "standard"): "advanced",
            ("intermediate", "advanced"): "advanced",
            ("advanced", "basic"): "basic",
            ("advanced", "standard"): "advanced",
            ("advanced", "advanced"): "advanced"
        }
        
        return analysis_mapping.get((experience_level, analysis_depth), "basic")
    
    def _determine_session_analysis_type(self, experience_level: str, analysis_type: str) -> str:
        """
        Determine the appropriate session analysis type based on experience level.
        
        Implements adaptive analysis depth for sessions (requirement 7.8).
        """
        if experience_level == "beginner":
            return "quick_review"  # Simpler analysis for beginners
        elif experience_level == "intermediate":
            return analysis_type  # Use requested type
        else:  # advanced
            if analysis_type == "summary":
                return "summary"  # Can handle full summary
            else:
                return analysis_type
    
    def _prepare_comprehensive_hand_data(
        self, 
        hand: HandResponse, 
        experience_level: str, 
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Prepare comprehensive hand data with decision point analysis.
        
        Implements strategic advice for each decision point (requirement 7.1).
        """
        base_data = self._prepare_hand_data(hand, experience_level)
        
        # Add decision point analysis
        decision_points = self._extract_decision_points(hand)
        base_data.update({
            'decision_points': decision_points,
            'focus_areas': ', '.join(focus_areas) if focus_areas else 'general analysis',
            'key_decisions': self._identify_key_decisions(hand, decision_points),
            'street_analysis': self._prepare_street_analysis(hand),
            'position_context': self._get_position_context(hand),
            'stack_dynamics': self._analyze_stack_dynamics(hand),
            'betting_patterns': self._analyze_betting_patterns(hand)
        })
        
        return base_data
    
    def _prepare_comprehensive_session_data(
        self, 
        hands: List[HandResponse], 
        session_stats: Dict[str, Any],
        experience_level: str,
        include_individual_hands: bool = True
    ) -> Dict[str, Any]:
        """
        Prepare comprehensive session data with individual hand breakdowns.
        
        Implements hand-by-hand breakdowns (requirement 7.6).
        """
        base_data = self._prepare_session_data(hands, session_stats)
        
        # Add comprehensive session analysis data
        base_data.update({
            'experience_level': experience_level,
            'decision_quality': self._assess_session_decision_quality(hands),
            'leak_analysis': self._identify_session_leaks(hands, session_stats),
            'strength_analysis': self._identify_session_strengths(hands, session_stats),
            'improvement_priorities': self._prioritize_improvements(hands, session_stats, experience_level),
            'hand_categories': self._categorize_session_hands(hands),
            'learning_opportunities': self._identify_learning_hands(hands)
        })
        
        if include_individual_hands:
            base_data['individual_hand_summaries'] = self._create_hand_summaries(hands)
        
        return base_data
    
    def _extract_decision_points(self, hand: HandResponse) -> List[Dict[str, Any]]:
        """Extract key decision points from a hand for analysis."""
        decision_points = []
        
        if not hand.actions:
            return decision_points
        
        # Handle actions stored as dict (by street) or list
        if isinstance(hand.actions, dict):
            # Actions organized by street
            for street, street_actions in hand.actions.items():
                if isinstance(street_actions, list):
                    hero_actions = [a for a in street_actions if isinstance(a, dict) and a.get('player') == 'Hero']
                    for action in hero_actions:
                        decision_points.append({
                            'street': street,
                            'action': action.get('action', 'unknown'),
                            'amount': action.get('amount'),
                            'position': hand.position,
                            'context': f"{street} decision",
                            'board_cards': hand.board_cards if street != 'preflop' else [],
                            'pot_size_before': action.get('pot_before', 0)
                        })
        elif isinstance(hand.actions, list):
            # Actions as flat list
            for action in hand.actions:
                if isinstance(action, dict) and action.get('player') == 'Hero':
                    street = action.get('street', 'preflop')
                    decision_points.append({
                        'street': street,
                        'action': action.get('action', 'unknown'),
                        'amount': action.get('amount'),
                        'position': hand.position,
                        'context': f"{street} decision",
                        'board_cards': hand.board_cards if street != 'preflop' else [],
                        'pot_size_before': action.get('pot_before', 0)
                    })
        
        return decision_points
    
    def _identify_key_decisions(self, hand: HandResponse, decision_points: List[Dict[str, Any]]) -> str:
        """Identify the most important decisions in the hand."""
        if not decision_points:
            return "No key decisions identified"
        
        key_decisions = []
        for dp in decision_points:
            if dp['action'] in ['bet', 'raise', 'call', 'fold']:
                street = dp['street']
                action = dp['action']
                amount = dp.get('amount', 0)
                
                if amount and amount > 0:
                    key_decisions.append(f"{street}: {action} ${amount}")
                else:
                    key_decisions.append(f"{street}: {action}")
        
        return '; '.join(key_decisions) if key_decisions else "Standard play throughout"
    
    def _prepare_street_analysis(self, hand: HandResponse) -> Dict[str, str]:
        """Prepare street-by-street analysis context."""
        streets = {
            'preflop': 'Position and hand selection analysis',
            'flop': 'Board texture and continuation betting',
            'turn': 'Hand development and value/bluff decisions',
            'river': 'Final value extraction and bluff catching'
        }
        
        # Add actual board cards for postflop streets
        if hand.board_cards and len(hand.board_cards) >= 3:
            flop_cards = hand.board_cards[:3]
            streets['flop'] = f"Flop ({' '.join(flop_cards)}): Board texture analysis"
            
            if len(hand.board_cards) >= 4:
                turn_card = hand.board_cards[3]
                streets['turn'] = f"Turn ({turn_card}): Hand development analysis"
                
                if len(hand.board_cards) >= 5:
                    river_card = hand.board_cards[4]
                    streets['river'] = f"River ({river_card}): Final decision analysis"
        
        return streets
    
    def _get_position_context(self, hand: HandResponse) -> str:
        """Get position-specific context for analysis."""
        position = hand.position or "Unknown"
        
        position_contexts = {
            'UTG': 'Early position - tight range required',
            'MP': 'Middle position - balanced approach',
            'CO': 'Cutoff - wider range opportunities',
            'BTN': 'Button - maximum positional advantage',
            'SB': 'Small blind - difficult position postflop',
            'BB': 'Big blind - defending range considerations'
        }
        
        return position_contexts.get(position, f"{position} position analysis")
    
    def _analyze_stack_dynamics(self, hand: HandResponse) -> str:
        """Analyze stack size implications."""
        if not hand.player_stacks:
            return "Stack information not available"
        
        # This would analyze effective stacks, SPR, etc.
        return "Stack dynamics analysis based on effective stacks and pot size"
    
    def _analyze_betting_patterns(self, hand: HandResponse) -> str:
        """Analyze betting patterns and sizing."""
        if not hand.actions:
            return "No betting pattern analysis available"
        
        # This would analyze bet sizing, aggression, etc.
        return "Betting pattern analysis including sizing and timing"
    
    def _assess_session_decision_quality(self, hands: List[HandResponse]) -> Dict[str, Any]:
        """Assess overall decision quality across the session."""
        total_decisions = 0
        decision_categories = {
            'preflop': 0,
            'postflop': 0,
            'aggressive': 0,
            'passive': 0
        }
        
        for hand in hands:
            if hand.actions:
                # Handle both dict and list formats
                if isinstance(hand.actions, dict):
                    # Actions organized by street
                    for street, street_actions in hand.actions.items():
                        if isinstance(street_actions, list):
                            for action in street_actions:
                                if isinstance(action, dict) and action.get('player') == 'Hero':
                                    total_decisions += 1
                                    action_type = action.get('action', 'unknown')
                                    
                                    if street == 'preflop':
                                        decision_categories['preflop'] += 1
                                    else:
                                        decision_categories['postflop'] += 1
                                    
                                    if action_type in ['bet', 'raise']:
                                        decision_categories['aggressive'] += 1
                                    elif action_type in ['call', 'check']:
                                        decision_categories['passive'] += 1
                elif isinstance(hand.actions, list):
                    # Actions as flat list
                    for action in hand.actions:
                        if isinstance(action, dict) and action.get('player') == 'Hero':
                            total_decisions += 1
                            street = action.get('street', 'preflop')
                            action_type = action.get('action', 'unknown')
                            
                            if street == 'preflop':
                                decision_categories['preflop'] += 1
                            else:
                                decision_categories['postflop'] += 1
                            
                            if action_type in ['bet', 'raise']:
                                decision_categories['aggressive'] += 1
                            elif action_type in ['call', 'check']:
                                decision_categories['passive'] += 1
        
        return {
            'total_decisions': total_decisions,
            'decision_breakdown': decision_categories,
            'aggression_ratio': decision_categories['aggressive'] / max(total_decisions, 1)
        }
    
    def _identify_session_leaks(self, hands: List[HandResponse], session_stats: Dict[str, Any]) -> List[str]:
        """Identify potential leaks from session data."""
        leaks = []
        
        # Check VPIP
        vpip = session_stats.get('vpip', 0)
        if vpip > 35:
            leaks.append("Playing too many hands (high VPIP)")
        elif vpip < 15:
            leaks.append("Playing too tight (low VPIP)")
        
        # Check aggression
        aggression = session_stats.get('aggression_factor', 0)
        if aggression < 1:
            leaks.append("Too passive - not betting/raising enough")
        elif aggression > 4:
            leaks.append("Overly aggressive - may be bluffing too much")
        
        # Check PFR vs VPIP
        pfr = session_stats.get('pfr', 0)
        if vpip > 0 and pfr / vpip < 0.6:
            leaks.append("Too much calling preflop - should raise or fold more")
        
        return leaks if leaks else ["No major leaks identified"]
    
    def _identify_session_strengths(self, hands: List[HandResponse], session_stats: Dict[str, Any]) -> List[str]:
        """Identify strengths from session data."""
        strengths = []
        
        # Check win rate
        win_rate = session_stats.get('win_rate', 0)
        if win_rate > 0:
            strengths.append("Positive win rate - profitable session")
        
        # Check balanced stats
        vpip = session_stats.get('vpip', 0)
        pfr = session_stats.get('pfr', 0)
        if 20 <= vpip <= 30 and 15 <= pfr <= 25:
            strengths.append("Balanced preflop ranges")
        
        # Check aggression
        aggression = session_stats.get('aggression_factor', 0)
        if 2 <= aggression <= 3:
            strengths.append("Good aggression balance")
        
        return strengths if strengths else ["Session shows room for improvement"]
    
    def _prioritize_improvements(self, hands: List[HandResponse], session_stats: Dict[str, Any], experience_level: str) -> List[str]:
        """Prioritize improvement areas based on experience level."""
        improvements = []
        
        # Get leaks first
        leaks = self._identify_session_leaks(hands, session_stats)
        
        # Prioritize based on experience level
        if experience_level == "beginner":
            improvements.extend([
                "Focus on tight-aggressive play",
                "Study basic preflop ranges",
                "Practice position awareness"
            ])
        elif experience_level == "intermediate":
            improvements.extend([
                "Refine postflop decision making",
                "Improve bet sizing",
                "Study opponent tendencies"
            ])
        else:  # advanced
            improvements.extend([
                "Advanced range analysis",
                "Exploitative adjustments",
                "Mental game optimization"
            ])
        
        # Add leak-specific improvements
        improvements.extend(leaks[:3])  # Top 3 leaks
        
        return improvements[:5]  # Return top 5 priorities
    
    def _categorize_session_hands(self, hands: List[HandResponse]) -> Dict[str, int]:
        """Categorize hands by type for analysis."""
        categories = {
            'premium_hands': 0,
            'speculative_hands': 0,
            'bluff_attempts': 0,
            'value_bets': 0,
            'defensive_plays': 0
        }
        
        # This would analyze each hand and categorize
        # For now, return basic categorization
        total_hands = len(hands)
        categories['premium_hands'] = int(total_hands * 0.15)  # Estimate
        categories['speculative_hands'] = int(total_hands * 0.25)
        categories['value_bets'] = int(total_hands * 0.30)
        categories['defensive_plays'] = int(total_hands * 0.20)
        categories['bluff_attempts'] = total_hands - sum(categories.values())
        
        return categories
    
    def _identify_learning_hands(self, hands: List[HandResponse]) -> List[Dict[str, Any]]:
        """Identify hands with the most learning potential."""
        learning_hands = []
        
        # Select hands with interesting decision points
        for i, hand in enumerate(hands[:5]):  # Limit to first 5 for analysis
            if hand.actions and len(hand.actions) > 2:  # Hands with multiple actions
                learning_hands.append({
                    'hand_id': hand.hand_id,
                    'position': hand.position,
                    'cards': hand.player_cards,
                    'result': hand.result,
                    'learning_focus': 'Multi-street decision making'
                })
        
        return learning_hands
    
    def _create_hand_summaries(self, hands: List[HandResponse]) -> List[Dict[str, Any]]:
        """Create brief summaries of individual hands."""
        summaries = []
        
        for hand in hands[:10]:  # Limit to 10 hands for performance
            summary = {
                'hand_id': hand.hand_id,
                'position': hand.position,
                'cards': hand.player_cards,
                'result': hand.result,
                'key_action': self._get_key_action(hand),
                'outcome': 'Won' if hand.result and 'won' in hand.result.lower() else 'Lost'
            }
            summaries.append(summary)
        
        return summaries
    
    def _get_key_action(self, hand: HandResponse) -> str:
        """Get the most significant action from a hand."""
        if not hand.actions:
            return "No action recorded"
        
        hero_actions = []
        
        # Handle both dict and list formats
        if isinstance(hand.actions, dict):
            # Actions organized by street
            for street_actions in hand.actions.values():
                if isinstance(street_actions, list):
                    hero_actions.extend([a for a in street_actions if isinstance(a, dict) and a.get('player') == 'Hero'])
        elif isinstance(hand.actions, list):
            # Actions as flat list
            hero_actions = [a for a in hand.actions if isinstance(a, dict) and a.get('player') == 'Hero']
        
        if not hero_actions:
            return "No hero actions"
        
        # Find the largest bet/raise by Hero
        largest_action = max(hero_actions, key=lambda x: x.get('amount', 0) if x.get('amount') else 0)
        action_type = largest_action.get('action', 'unknown')
        amount = largest_action.get('amount')
        
        if amount:
            return f"{action_type} ${amount}"
        else:
            return action_type
    
    def _extract_structured_insights(self, analysis_content: str, analysis_type: str) -> Dict[str, Any]:
        """
        Extract structured insights from AI analysis content.
        
        This helps organize the analysis into actionable components.
        """
        insights = {
            'key_points': [],
            'recommendations': [],
            'strengths': [],
            'weaknesses': [],
            'learning_focus': []
        }
        
        if not analysis_content:
            return insights
        
        # Simple extraction based on common patterns
        lines = analysis_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections
            if 'recommendation' in line.lower() or 'suggest' in line.lower():
                current_section = 'recommendations'
            elif 'strength' in line.lower() or 'good' in line.lower():
                current_section = 'strengths'
            elif 'weakness' in line.lower() or 'mistake' in line.lower():
                current_section = 'weaknesses'
            elif 'learn' in line.lower() or 'focus' in line.lower():
                current_section = 'learning_focus'
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')):
                if current_section:
                    insights[current_section].append(line)
                else:
                    insights['key_points'].append(line)
        
        return insights
    
    def _extract_session_insights(self, analysis_content: str, analysis_type: str) -> Dict[str, Any]:
        """
        Extract structured insights from session analysis content.
        """
        insights = {
            'session_summary': '',
            'major_patterns': [],
            'improvement_areas': [],
            'positive_trends': [],
            'action_items': []
        }
        
        if not analysis_content:
            return insights
        
        # Extract first paragraph as summary
        paragraphs = analysis_content.split('\n\n')
        if paragraphs:
            insights['session_summary'] = paragraphs[0].strip()
        
        # Simple pattern extraction
        lines = analysis_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if 'pattern' in line.lower():
                insights['major_patterns'].append(line)
            elif 'improve' in line.lower() or 'work on' in line.lower():
                insights['improvement_areas'].append(line)
            elif 'good' in line.lower() or 'strength' in line.lower():
                insights['positive_trends'].append(line)
            elif 'action' in line.lower() or 'next' in line.lower():
                insights['action_items'].append(line)
        
        return insights

    def _prepare_hand_data(self, hand: HandResponse, experience_level: str) -> Dict[str, Any]:
        """Prepare hand data for prompt formatting."""
        return {
            'platform': hand.platform,
            'game_type': hand.game_type,
            'stakes': hand.stakes,
            'position': hand.position,
            'player_cards': ', '.join(hand.player_cards) if hand.player_cards else 'Unknown',
            'board_cards': ', '.join(hand.board_cards) if hand.board_cards else 'None',
            'actions': self._format_actions(hand.actions),
            'result': hand.result,
            'pot_size': f"${hand.pot_size}" if hand.pot_size else "Unknown",
            'experience_level': experience_level,
            'stack_info': self._format_stack_info(hand),
            'detailed_actions': self._format_detailed_actions(hand.actions),
            'tournament_info': self._format_tournament_info(hand),
            'player_stats': "Not available"  # Would be populated from user stats
        }
    
    def _prepare_session_data(self, hands: List[HandResponse], session_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare session data for prompt formatting."""
        session_length = len(hands)
        
        # Calculate session duration
        if hands and len(hands) > 1:
            # Use created_at instead of timestamp
            start_time = min(hand.created_at for hand in hands if hand.created_at)
            end_time = max(hand.created_at for hand in hands if hand.created_at)
            duration = end_time - start_time if start_time and end_time else None
            time_duration = str(duration) if duration else "Unknown"
        else:
            time_duration = "Single hand"
        
        return {
            'session_length': session_length,
            'time_duration': time_duration,
            'vpip': session_stats.get('vpip', 0),
            'pfr': session_stats.get('pfr', 0),
            'aggression_factor': session_stats.get('aggression_factor', 0),
            'win_rate': session_stats.get('win_rate', 0),
            'three_bet_pct': session_stats.get('three_bet_percentage', 0),
            'cbet_pct': session_stats.get('cbet_flop', 0),
            'significant_hands_count': min(5, session_length),  # Limit to top 5 hands
            'session_results': self._format_session_results(session_stats),
            'session_patterns': self._identify_session_patterns(hands, session_stats)
        }
    
    def _format_actions(self, actions: Dict[str, Any]) -> str:
        """Format actions for prompt display."""
        if not actions:
            return "No actions recorded"
        
        formatted = []
        
        # Handle actions stored as dict (by street) or list
        if isinstance(actions, dict):
            # Actions organized by street
            for street, street_actions in actions.items():
                if isinstance(street_actions, list):
                    for action in street_actions:
                        if isinstance(action, dict):
                            player = action.get('player', 'Unknown')
                            action_type = action.get('action', 'unknown')
                            amount = action.get('amount')
                            
                            if amount:
                                formatted.append(f"{player} {action_type}s ${amount} on {street}")
                            else:
                                formatted.append(f"{player} {action_type}s on {street}")
        elif isinstance(actions, list):
            # Actions as flat list
            for action in actions:
                if isinstance(action, dict):
                    player = action.get('player', 'Unknown')
                    action_type = action.get('action', 'unknown')
                    amount = action.get('amount')
                    street = action.get('street', 'preflop')
                    
                    if amount:
                        formatted.append(f"{player} {action_type}s ${amount} on {street}")
                    else:
                        formatted.append(f"{player} {action_type}s on {street}")
        
        return '; '.join(formatted) if formatted else "No actions recorded"
    
    def _format_detailed_actions(self, actions: Dict[str, Any]) -> str:
        """Format detailed actions with more context."""
        if not actions:
            return "No detailed actions available"
        
        formatted_streets = []
        
        # Handle actions stored as dict (by street) or list
        if isinstance(actions, dict):
            # Actions already organized by street
            for street, street_actions in actions.items():
                if isinstance(street_actions, list):
                    street_desc = f"{street.title()}: "
                    action_descs = []
                    for action in street_actions:
                        if isinstance(action, dict):
                            player = action.get('player', 'Unknown')
                            action_type = action.get('action', 'unknown')
                            amount = action.get('amount')
                            if amount:
                                action_descs.append(f"{player} {action_type}s ${amount}")
                            else:
                                action_descs.append(f"{player} {action_type}s")
                    street_desc += ', '.join(action_descs)
                    formatted_streets.append(street_desc)
        elif isinstance(actions, list):
            # Group actions by street first
            streets = {}
            for action in actions:
                if isinstance(action, dict):
                    street = action.get('street', 'preflop')
                    if street not in streets:
                        streets[street] = []
                    streets[street].append(action)
            
            for street, street_actions in streets.items():
                street_desc = f"{street.title()}: "
                action_descs = []
                for action in street_actions:
                    if isinstance(action, dict):
                        player = action.get('player', 'Unknown')
                        action_type = action.get('action', 'unknown')
                        amount = action.get('amount')
                        if amount:
                            action_descs.append(f"{player} {action_type}s ${amount}")
                        else:
                            action_descs.append(f"{player} {action_type}s")
                street_desc += ', '.join(action_descs)
                formatted_streets.append(street_desc)
        
        return '\n'.join(formatted_streets) if formatted_streets else "No detailed actions available"
    
    def _format_stack_info(self, hand: HandResponse) -> str:
        """Format stack information."""
        if not hand.player_stacks:
            return "Stack information not available"
        
        # Format player stacks
        stack_info = []
        if hand.player_stacks and isinstance(hand.player_stacks, dict):
            # Handle JSONB field that might be stored as dict
            for player, stack in hand.player_stacks.items():
                stack_info.append(f"{player}: ${stack}")
        elif hand.player_stacks and isinstance(hand.player_stacks, list):
            # Handle if it's a list of stack objects
            for stack in hand.player_stacks:
                if isinstance(stack, dict):
                    player = stack.get('player', 'Unknown')
                    amount = stack.get('stack', 0)
                    stack_info.append(f"{player}: ${amount}")
        
        return ', '.join(stack_info) if stack_info else "Stack information not available"
    
    def _format_tournament_info(self, hand: HandResponse) -> str:
        """Format tournament information."""
        if not hand.tournament_info:
            return "Cash game"
        
        if isinstance(hand.tournament_info, dict):
            info = hand.tournament_info
            return f"Tournament: {info.get('tournament_id', 'Unknown')}, Level: {info.get('level', 'Unknown')}"
        else:
            return "Tournament information available"
    
    def _format_session_results(self, session_stats: Dict[str, Any]) -> str:
        """Format session results summary."""
        win_rate = session_stats.get('win_rate', 0)
        hands_played = session_stats.get('hands_played', 0)
        
        if win_rate > 0:
            return f"Winning session: +{win_rate} BB/100 over {hands_played} hands"
        elif win_rate < 0:
            return f"Losing session: {win_rate} BB/100 over {hands_played} hands"
        else:
            return f"Break-even session over {hands_played} hands"
    
    def _identify_session_patterns(self, hands: List[HandResponse], session_stats: Dict[str, Any]) -> str:
        """Identify notable patterns in the session."""
        patterns = []
        
        # Check for high/low VPIP
        vpip = session_stats.get('vpip', 0)
        if vpip > 30:
            patterns.append("Playing very loose (high VPIP)")
        elif vpip < 15:
            patterns.append("Playing very tight (low VPIP)")
        
        # Check aggression
        aggression = session_stats.get('aggression_factor', 0)
        if aggression > 3:
            patterns.append("Very aggressive play")
        elif aggression < 1:
            patterns.append("Passive play style")
        
        # Check for position-based patterns
        position_counts = {}
        for hand in hands:
            pos = hand.position
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        if position_counts:
            most_common_pos = max(position_counts, key=position_counts.get)
            patterns.append(f"Most hands played from {most_common_pos} position")
        
        return '; '.join(patterns) if patterns else "No notable patterns identified"
    
    async def validate_api_key(self, provider: AIProvider, api_key: str) -> bool:
        """
        Validate an API key for the specified provider.
        
        Args:
            provider: AI provider to validate
            api_key: API key to validate
            
        Returns:
            True if API key is valid, False otherwise
        """
        try:
            return await AIProviderFactory.validate_api_key(provider, api_key)
        except Exception as e:
            logger.error(f"Error validating API key for {provider}: {e}")
            return False
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of available AI providers."""
        return AIProviderFactory.get_available_providers()
    
    def get_provider_capabilities(self, provider: AIProvider) -> Dict[str, Any]:
        """Get capabilities for a specific provider."""
        return PROVIDER_CAPABILITIES.get(provider, {})
    
    def get_default_models(self) -> Dict[AIProvider, str]:
        """Get default models for each provider."""
        return AIProviderFactory.get_default_models()
    
    def clear_client_cache(self) -> None:
        """Clear the client cache (useful for testing or key rotation)."""
        self._client_cache.clear()
    
    def get_available_analysis_types(self) -> Dict[str, List[str]]:
        """Get available analysis types from loaded prompts."""
        available = {}
        
        for category in self.prompt_manager.get_available_categories():
            available[category] = self.prompt_manager.get_available_types(category)
        
        return available
    
    def validate_analysis_request(self, category: str, analysis_type: str) -> bool:
        """Validate that an analysis request is supported."""
        return self.prompt_manager.validate_prompt_structure(category, analysis_type)


# Global AI analysis service instance
_ai_analysis_service: Optional[AIAnalysisService] = None


def get_ai_analysis_service() -> AIAnalysisService:
    """Get the global AI analysis service instance."""
    global _ai_analysis_service
    if _ai_analysis_service is None:
        _ai_analysis_service = AIAnalysisService()
    return _ai_analysis_service