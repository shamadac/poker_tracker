"""
Property-Based Tests for Comprehensive AI Analysis with YAML Prompts

**Feature: professional-poker-analyzer-rebuild, Property 17: Comprehensive AI Analysis with YAML Prompts**

Tests the universal property that for any poker hand or session analysis, the system 
should load prompts from YAML configuration files and provide strategic advice, 
identify strengths and weaknesses, highlight improvement areas, and generate executive 
summaries with appropriate depth based on user experience level.

**Validates: Requirements 7.1, 7.2, 7.4, 7.6, 7.7, 7.8**

This test ensures that:
1. YAML prompts are loaded and used correctly for analysis
2. Strategic advice is provided for each decision point (7.1)
3. Strengths and weaknesses are identified (7.2, 7.4)
4. Hand-by-hand breakdowns are provided (7.6)
5. Executive summaries are generated (7.7)
6. Analysis depth adapts to user experience level (7.8)
7. Analysis results are comprehensive and structured
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from app.services.ai_analysis import AIAnalysisService, AnalysisResult
from app.services.ai_providers import AIProvider, AIResponse
from app.schemas.hand import HandResponse


# Test data strategies
@st.composite
def comprehensive_hand_data(draw):
    """Generate comprehensive hand data for testing."""
    return HandResponse(
        # Required fields
        id=str(draw(st.uuids())),
        created_at=draw(st.datetimes()),
        updated_at=draw(st.datetimes()),
        hand_id=draw(st.text(min_size=5, max_size=20)),
        platform=draw(st.sampled_from(['pokerstars', 'ggpoker'])),
        user_id=str(draw(st.uuids())),
        
        # Comprehensive optional fields for analysis
        game_type=draw(st.sampled_from(['No Limit Hold\'em', 'Pot Limit Omaha', 'Tournament'])),
        game_format=draw(st.sampled_from(['tournament', 'cash', 'sng'])),
        stakes=draw(st.sampled_from(['$0.01/$0.02', '$0.05/$0.10', '$1/$2', '$5/$10'])),
        position=draw(st.sampled_from(['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'])),
        player_cards=draw(st.lists(st.text(min_size=2, max_size=2), min_size=2, max_size=2)),
        board_cards=draw(st.lists(st.text(min_size=2, max_size=2), min_size=0, max_size=5)),
        
        # Complex actions for decision point analysis
        actions=draw(st.dictionaries(
            st.sampled_from(['preflop', 'flop', 'turn', 'river']),
            st.lists(st.dictionaries(
                st.sampled_from(['player', 'action', 'amount', 'street', 'position']),
                st.one_of(
                    st.text(min_size=1, max_size=10),
                    st.sampled_from(['fold', 'check', 'call', 'bet', 'raise', 'all-in']),
                    st.integers(min_value=0, max_value=1000),
                    st.sampled_from(['preflop', 'flop', 'turn', 'river']),
                    st.sampled_from(['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'])
                )
            ), min_size=1, max_size=8),
            min_size=1, max_size=4
        )),
        
        result=draw(st.sampled_from(['won', 'lost', 'folded', 'split'])),
        pot_size=draw(st.floats(min_value=1.0, max_value=1000.0)),
        
        # Stack information for strategic analysis
        player_stacks=draw(st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=100, max_value=10000),
            min_size=2, max_size=9
        )),
        
        # Tournament info for ICM considerations
        tournament_info=draw(st.one_of(
            st.none(),
            st.dictionaries(
                st.sampled_from(['tournament_id', 'level', 'blinds', 'players_remaining']),
                st.one_of(
                    st.text(min_size=1, max_size=20),
                    st.integers(min_value=1, max_value=1000)
                ),
                min_size=1, max_size=4
            )
        )),
        
        analysis_count=0,
        is_play_money=False
    )


@st.composite
def session_data_comprehensive(draw):
    """Generate comprehensive session data for testing."""
    hands_count = draw(st.integers(min_value=1, max_value=20))
    hands = [draw(comprehensive_hand_data()) for _ in range(hands_count)]
    
    session_stats = {
        'hands_played': hands_count,
        'vpip': draw(st.floats(min_value=10.0, max_value=40.0)),
        'pfr': draw(st.floats(min_value=8.0, max_value=30.0)),
        'aggression_factor': draw(st.floats(min_value=0.5, max_value=5.0)),
        'win_rate': draw(st.floats(min_value=-10.0, max_value=15.0)),
        'three_bet_percentage': draw(st.floats(min_value=2.0, max_value=12.0)),
        'cbet_flop': draw(st.floats(min_value=40.0, max_value=90.0)),
        'fold_to_cbet_flop': draw(st.floats(min_value=30.0, max_value=80.0)),
        'check_raise_flop': draw(st.floats(min_value=5.0, max_value=25.0))
    }
    
    return hands, session_stats


@st.composite
def analysis_configuration(draw):
    """Generate analysis configuration parameters."""
    return {
        'provider': draw(st.sampled_from([AIProvider.GEMINI, AIProvider.GROQ])),
        'experience_level': draw(st.sampled_from(['beginner', 'intermediate', 'advanced'])),
        'analysis_depth': draw(st.sampled_from(['basic', 'standard', 'advanced'])),
        'focus_areas': draw(st.lists(
            st.sampled_from([
                'decision_making', 'position_play', 'bet_sizing', 'bluff_catching',
                'value_betting', 'tournament_strategy', 'cash_game_strategy'
            ]),
            min_size=0, max_size=4
        )),
        'temperature': draw(st.floats(min_value=0.1, max_value=1.0)),
        'max_tokens': draw(st.integers(min_value=500, max_value=4000))
    }


class TestComprehensiveAnalysisProperty:
    """Property-based tests for comprehensive AI analysis system."""
    
    def setup_method(self):
        """Set up test environment."""
        # Disable logging during tests to reduce noise
        logging.getLogger('app.services.ai_analysis').setLevel(logging.CRITICAL)
        logging.getLogger('app.services.prompt_manager').setLevel(logging.CRITICAL)
    
    @given(comprehensive_hand_data(), analysis_configuration())
    @settings(max_examples=50, deadline=10000)
    async def test_property_comprehensive_hand_analysis_structure(self, hand_data, config):
        """
        Property: For any hand analysis request, the system should provide 
        comprehensive analysis with strategic advice, strengths/weaknesses 
        identification, and structured insights.
        """
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock comprehensive YAML prompt loading
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': f'You are a comprehensive poker analyst for {config["experience_level"]} players.',
                'user': f'Analyze hand {hand_data.hand_id} with focus on {", ".join(config["focus_areas"]) if config["focus_areas"] else "general analysis"}',
                'metadata': {'analysis_type': 'comprehensive'}
            }
            
            # Mock comprehensive AI response with structured content
            comprehensive_content = self._generate_comprehensive_analysis_content(
                hand_data, config['experience_level'], config['focus_areas']
            )
            
            mock_response = AIResponse(
                success=True,
                content=comprehensive_content,
                provider=config['provider'],
                usage={'prompt_tokens': 400, 'completion_tokens': 1200, 'total_tokens': 1600},
                metadata={'model': 'test-model', 'analysis_depth': config['analysis_depth']}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Comprehensive analysis should succeed
                    result = await analysis_service.analyze_hand_comprehensive(
                        hand_data,
                        config['provider'],
                        'test_api_key',
                        experience_level=config['experience_level'],
                        analysis_depth=config['analysis_depth'],
                        focus_areas=config['focus_areas'],
                        temperature=config['temperature'],
                        max_tokens=config['max_tokens']
                    )
                    
                    # Property: Result should be successful and comprehensive
                    assert isinstance(result, AnalysisResult)
                    assert result.success is True
                    assert result.provider == config['provider']
                    assert result.content is not None
                    
                    # Property: Content should contain strategic advice (7.1)
                    content_lower = result.content.lower()
                    strategic_indicators = ['decision', 'strategy', 'recommend', 'should', 'consider']
                    assert any(indicator in content_lower for indicator in strategic_indicators), \
                        "Analysis should contain strategic advice"
                    
                    # Property: Content should identify strengths and weaknesses (7.2, 7.4)
                    analysis_indicators = ['strength', 'weakness', 'good', 'mistake', 'improve']
                    assert any(indicator in content_lower for indicator in analysis_indicators), \
                        "Analysis should identify strengths and weaknesses"
                    
                    # Property: Metadata should reflect comprehensive analysis
                    assert result.metadata is not None
                    assert result.metadata['analysis_depth'] == config['analysis_depth']
                    assert result.metadata['experience_level'] == config['experience_level']
                    assert 'focus_areas' in result.metadata
                    assert 'structured_insights' in result.metadata
                    
                    # Property: Structured insights should be present
                    insights = result.metadata['structured_insights']
                    assert isinstance(insights, dict)
                    expected_insight_keys = ['key_points', 'recommendations', 'strengths', 'weaknesses']
                    for key in expected_insight_keys:
                        assert key in insights
    
    @given(session_data_comprehensive(), analysis_configuration())
    @settings(max_examples=30, deadline=15000)
    async def test_property_comprehensive_session_analysis_structure(self, session_data, config):
        """
        Property: For any session analysis request, the system should provide 
        comprehensive session analysis with hand-by-hand breakdowns and 
        executive summaries.
        """
        hands, session_stats = session_data
        
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock session analysis YAML prompt loading
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': f'You are a comprehensive session analyst for {config["experience_level"]} players.',
                'user': f'Analyze session of {len(hands)} hands with comprehensive breakdown',
                'metadata': {'analysis_type': 'comprehensive_session'}
            }
            
            # Mock comprehensive session analysis response
            session_content = self._generate_comprehensive_session_content(
                hands, session_stats, config['experience_level']
            )
            
            mock_response = AIResponse(
                success=True,
                content=session_content,
                provider=config['provider'],
                usage={'prompt_tokens': 600, 'completion_tokens': 1800, 'total_tokens': 2400},
                metadata={'model': 'test-model', 'session_type': 'comprehensive'}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Comprehensive session analysis should succeed
                    result = await analysis_service.analyze_session_comprehensive(
                        hands,
                        session_stats,
                        config['provider'],
                        'test_api_key',
                        analysis_type='summary',
                        experience_level=config['experience_level'],
                        include_individual_hands=True,
                        temperature=config['temperature'],
                        max_tokens=config['max_tokens']
                    )
                    
                    # Property: Result should be successful and comprehensive
                    assert isinstance(result, AnalysisResult)
                    assert result.success is True
                    assert result.provider == config['provider']
                    assert result.content is not None
                    
                    # Property: Content should contain executive summary (7.7)
                    content_lower = result.content.lower()
                    summary_indicators = ['summary', 'overall', 'session', 'performance', 'conclusion']
                    assert any(indicator in content_lower for indicator in summary_indicators), \
                        "Analysis should contain executive summary"
                    
                    # Property: Content should contain hand-by-hand insights (7.6)
                    breakdown_indicators = ['hand', 'decision', 'breakdown', 'individual', 'specific']
                    assert any(indicator in content_lower for indicator in breakdown_indicators), \
                        "Analysis should contain hand-by-hand breakdowns"
                    
                    # Property: Metadata should reflect comprehensive session analysis
                    assert result.metadata is not None
                    assert result.metadata['hands_count'] == len(hands)
                    assert result.metadata['experience_level'] == config['experience_level']
                    assert 'structured_insights' in result.metadata
                    
                    # Property: Session insights should be structured
                    insights = result.metadata['structured_insights']
                    assert isinstance(insights, dict)
                    session_insight_keys = ['session_summary', 'major_patterns', 'improvement_areas', 'action_items']
                    for key in session_insight_keys:
                        assert key in insights
    
    @given(comprehensive_hand_data(), st.sampled_from(['beginner', 'intermediate', 'advanced']))
    @settings(max_examples=40, deadline=10000)
    async def test_property_adaptive_analysis_depth(self, hand_data, experience_level):
        """
        Property: For any experience level, analysis depth should adapt 
        appropriately to provide suitable complexity and detail (7.8).
        """
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock adaptive prompt based on experience level
            if experience_level == 'beginner':
                system_prompt = 'You are a poker coach for beginners. Use simple language and focus on fundamentals.'
                expected_complexity = 'basic'
            elif experience_level == 'intermediate':
                system_prompt = 'You are a poker coach for intermediate players. Include strategic concepts and analysis.'
                expected_complexity = 'intermediate'
            else:  # advanced
                system_prompt = 'You are an expert poker strategist. Include advanced concepts, GTO analysis, and complex strategy.'
                expected_complexity = 'advanced'
            
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': system_prompt,
                'user': f'Analyze this hand for a {experience_level} player',
                'metadata': {'complexity': expected_complexity}
            }
            
            # Mock adaptive response content
            adaptive_content = self._generate_adaptive_analysis_content(hand_data, experience_level)
            
            mock_response = AIResponse(
                success=True,
                content=adaptive_content,
                provider=AIProvider.GEMINI,
                usage={'prompt_tokens': 300, 'completion_tokens': 900, 'total_tokens': 1200},
                metadata={'model': 'test-model', 'complexity': expected_complexity}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Analysis should adapt to experience level
                    result = await analysis_service.analyze_hand_comprehensive(
                        hand_data,
                        AIProvider.GEMINI,
                        'test_api_key',
                        experience_level=experience_level,
                        analysis_depth='standard'
                    )
                    
                    # Property: Result should be successful and adaptive
                    assert isinstance(result, AnalysisResult)
                    assert result.success is True
                    assert result.metadata['experience_level'] == experience_level
                    
                    # Property: Content complexity should match experience level
                    content_lower = result.content.lower()
                    
                    if experience_level == 'beginner':
                        # Beginner content should be simple and educational
                        beginner_indicators = ['basic', 'simple', 'fundamental', 'learn', 'understand']
                        assert any(indicator in content_lower for indicator in beginner_indicators), \
                            "Beginner analysis should use simple, educational language"
                    elif experience_level == 'intermediate':
                        # Intermediate content should include strategic concepts
                        intermediate_indicators = ['strategy', 'concept', 'consider', 'analyze', 'decision']
                        assert any(indicator in content_lower for indicator in intermediate_indicators), \
                            "Intermediate analysis should include strategic concepts"
                    else:  # advanced
                        # Advanced content should include complex analysis
                        advanced_indicators = ['gto', 'range', 'exploit', 'advanced', 'complex', 'optimal']
                        assert any(indicator in content_lower for indicator in advanced_indicators), \
                            "Advanced analysis should include complex strategic concepts"
    
    @given(comprehensive_hand_data(), analysis_configuration())
    @settings(max_examples=30, deadline=10000)
    async def test_property_yaml_prompt_integration(self, hand_data, config):
        """
        Property: For any analysis request, YAML prompts should be loaded 
        correctly and used to format analysis requests (7.1, 7.2).
        """
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            # Mock YAML prompt manager behavior
            expected_category = 'hand_analysis'
            
            # Determine expected type based on actual service logic
            if config['experience_level'] == 'beginner':
                expected_type = 'basic'  # Beginners always get basic
            elif config['experience_level'] == 'intermediate':
                if config['analysis_depth'] == 'basic':
                    expected_type = 'basic'
                else:  # standard or advanced
                    expected_type = 'advanced'
            else:  # advanced
                if config['analysis_depth'] == 'basic':
                    expected_type = 'basic'
                else:  # standard or advanced
                    expected_type = 'advanced'
            
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': f'YAML System Prompt for {expected_type} analysis',
                'user': f'YAML User Prompt with hand data: {hand_data.hand_id}',
                'metadata': {'source': 'yaml', 'category': expected_category, 'type': expected_type}
            }
            
            mock_response = AIResponse(
                success=True,
                content=f"Analysis using YAML prompts for {expected_type} level",
                provider=config['provider'],
                usage={'prompt_tokens': 200, 'completion_tokens': 600, 'total_tokens': 800},
                metadata={'model': 'test-model', 'prompt_source': 'yaml'}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: YAML prompts should be used correctly
                    result = await analysis_service.analyze_hand_comprehensive(
                        hand_data,
                        config['provider'],
                        'test_api_key',
                        experience_level=config['experience_level'],
                        analysis_depth=config['analysis_depth']
                    )
                    
                    # Property: Prompt manager should be called with correct parameters
                    mock_prompt_manager.return_value.format_prompt.assert_called_once()
                    call_args = mock_prompt_manager.return_value.format_prompt.call_args
                    
                    # Verify correct category and type were requested
                    assert call_args[0][0] == expected_category  # category
                    assert call_args[0][1] == expected_type      # prompt_type
                    
                    # Property: Result should contain YAML-sourced content
                    assert result.success is True
                    assert 'yaml' in result.content.lower()
                    assert result.prompt_used is not None
                    assert 'YAML' in result.prompt_used['system']
    
    @given(comprehensive_hand_data())
    @settings(max_examples=30, deadline=10000)
    async def test_property_improvement_areas_identification(self, hand_data):
        """
        Property: For any hand analysis, the system should identify specific 
        improvement areas and provide actionable recommendations (7.4).
        """
        with patch('app.services.ai_analysis.get_prompt_manager') as mock_prompt_manager:
            mock_prompt_manager.return_value.format_prompt.return_value = {
                'system': 'You are a poker coach focused on identifying improvement areas.',
                'user': f'Identify specific improvement areas for hand {hand_data.hand_id}',
                'metadata': {'focus': 'improvement'}
            }
            
            # Mock response with specific improvement areas
            improvement_content = self._generate_improvement_focused_content(hand_data)
            
            mock_response = AIResponse(
                success=True,
                content=improvement_content,
                provider=AIProvider.GEMINI,
                usage={'prompt_tokens': 250, 'completion_tokens': 750, 'total_tokens': 1000},
                metadata={'model': 'test-model', 'focus': 'improvement'}
            )
            
            # Create analysis service
            analysis_service = AIAnalysisService()
            
            with patch.object(analysis_service, '_get_or_create_client') as mock_get_client:
                mock_client = AsyncMock()
                mock_client.generate_response.return_value = mock_response
                mock_get_client.return_value = mock_client
                
                with patch.object(analysis_service, 'validate_api_key', return_value=True):
                    # Property: Analysis should identify improvement areas
                    result = await analysis_service.analyze_hand_comprehensive(
                        hand_data,
                        AIProvider.GEMINI,
                        'test_api_key',
                        experience_level='intermediate',
                        analysis_depth='standard'
                    )
                    
                    # Property: Result should contain improvement identification
                    assert result.success is True
                    content_lower = result.content.lower()
                    
                    # Property: Should highlight improvement areas (7.4)
                    improvement_indicators = [
                        'improve', 'better', 'should', 'could', 'recommend',
                        'mistake', 'error', 'suboptimal', 'adjustment'
                    ]
                    assert any(indicator in content_lower for indicator in improvement_indicators), \
                        "Analysis should highlight improvement areas"
                    
                    # Property: Should provide actionable recommendations
                    action_indicators = [
                        'next time', 'instead', 'try', 'practice', 'focus on',
                        'work on', 'study', 'consider', 'avoid'
                    ]
                    assert any(indicator in content_lower for indicator in action_indicators), \
                        "Analysis should provide actionable recommendations"
                    
                    # Property: Structured insights should include improvement areas
                    if 'structured_insights' in result.metadata:
                        insights = result.metadata['structured_insights']
                        assert 'recommendations' in insights
                        assert 'weaknesses' in insights
    
    def _generate_comprehensive_analysis_content(
        self, 
        hand_data: HandResponse, 
        experience_level: str, 
        focus_areas: List[str]
    ) -> str:
        """Generate realistic comprehensive analysis content."""
        content_parts = [
            f"Comprehensive Analysis for Hand {hand_data.hand_id}",
            "",
            "STRATEGIC DECISION ANALYSIS:",
            f"Position: {hand_data.position} - This position requires careful consideration of range and aggression.",
            f"Cards: {', '.join(hand_data.player_cards or ['Unknown'])} - Hand strength analysis and playability assessment.",
            "",
            "STRENGTHS IDENTIFIED:",
            "- Good position awareness demonstrated",
            "- Appropriate bet sizing for the situation",
            "- Solid fundamental decision making",
            "",
            "AREAS FOR IMPROVEMENT:",
            "- Could consider more aggressive line on the turn",
            "- Missed value betting opportunity on the river",
            "- Should analyze opponent tendencies more carefully",
            "",
            "KEY RECOMMENDATIONS:",
            "1. Focus on maximizing value in similar spots",
            "2. Study opponent betting patterns for future reference",
            "3. Consider range advantage when making decisions",
            "",
            f"EXPERIENCE LEVEL NOTES ({experience_level.upper()}):"
        ]
        
        if experience_level == 'beginner':
            content_parts.extend([
                "- Focus on basic hand selection and position play",
                "- Learn fundamental betting concepts",
                "- Practice reading board textures"
            ])
        elif experience_level == 'intermediate':
            content_parts.extend([
                "- Develop advanced positional strategy",
                "- Study opponent exploitation techniques",
                "- Improve bet sizing and value extraction"
            ])
        else:  # advanced
            content_parts.extend([
                "- Implement GTO-based decision making",
                "- Advanced range analysis and construction",
                "- Exploitative adjustments based on population tendencies"
            ])
        
        if focus_areas:
            content_parts.extend([
                "",
                f"FOCUS AREA ANALYSIS ({', '.join(focus_areas).upper()}):",
                "- Detailed analysis of requested focus areas",
                "- Specific recommendations for improvement",
                "- Practice exercises and study suggestions"
            ])
        
        return "\n".join(content_parts)
    
    def _generate_comprehensive_session_content(
        self, 
        hands: List[HandResponse], 
        session_stats: Dict[str, Any], 
        experience_level: str
    ) -> str:
        """Generate realistic comprehensive session analysis content."""
        hands_count = len(hands)
        vpip = session_stats.get('vpip', 25.0)
        win_rate = session_stats.get('win_rate', 0.0)
        
        content_parts = [
            f"COMPREHENSIVE SESSION ANALYSIS - {hands_count} Hands",
            "",
            "EXECUTIVE SUMMARY:",
            f"Session performance shows {'positive' if win_rate > 0 else 'negative'} results with {win_rate:.1f} BB/100 win rate.",
            f"VPIP of {vpip:.1f}% indicates {'loose' if vpip > 30 else 'tight' if vpip < 20 else 'balanced'} play style.",
            "Overall session demonstrates solid fundamental understanding with room for optimization.",
            "",
            "MAJOR PATTERNS IDENTIFIED:",
            "- Consistent position-based play throughout session",
            "- Good aggression balance in most situations",
            "- Some missed value betting opportunities in key spots",
            "",
            "HAND-BY-HAND BREAKDOWN HIGHLIGHTS:",
        ]
        
        # Add individual hand summaries
        for i, hand in enumerate(hands[:5]):  # Limit to first 5 hands
            content_parts.append(f"Hand #{i+1} ({hand.hand_id}): {hand.position} position, {hand.result} - Key decision analysis")
        
        if len(hands) > 5:
            content_parts.append(f"... and {len(hands) - 5} additional hands analyzed")
        
        content_parts.extend([
            "",
            "IMPROVEMENT PRIORITIES:",
            "1. Increase value betting frequency in strong spots",
            "2. Tighten up opening ranges from early position",
            "3. Improve river decision making and bluff catching",
            "",
            "ACTION ITEMS FOR NEXT SESSION:",
            "- Review hand histories for missed value bets",
            "- Practice range construction exercises",
            "- Study opponent tendencies and note-taking"
        ])
        
        return "\n".join(content_parts)
    
    def _generate_adaptive_analysis_content(self, hand_data: HandResponse, experience_level: str) -> str:
        """Generate analysis content adapted to experience level."""
        base_content = f"Analysis of Hand {hand_data.hand_id} for {experience_level} player"
        
        if experience_level == 'beginner':
            return f"{base_content}\n\nThis hand demonstrates basic poker fundamentals. The key learning points are simple and focus on understanding position, hand selection, and basic betting concepts. Remember to play tight from early position and be more aggressive when you have strong hands."
        
        elif experience_level == 'intermediate':
            return f"{base_content}\n\nThis hand requires strategic thinking about range construction and opponent analysis. Consider the betting patterns, position dynamics, and board texture when making decisions. Focus on developing your post-flop strategy and value betting concepts."
        
        else:  # advanced
            return f"{base_content}\n\nAdvanced analysis incorporating GTO principles and exploitative adjustments. Range analysis shows optimal play requires balancing value bets and bluffs in this spot. Consider population tendencies and implement solver-based strategies while maintaining exploitative adjustments against specific opponent types."
    
    def _generate_improvement_focused_content(self, hand_data: HandResponse) -> str:
        """Generate content focused on improvement areas identification."""
        return f"""Improvement Analysis for Hand {hand_data.hand_id}

SPECIFIC AREAS FOR IMPROVEMENT:

1. BET SIZING OPTIMIZATION
   - Current sizing could be improved for better value extraction
   - Consider using larger sizes with strong hands
   - Recommend studying optimal sizing charts

2. DECISION TIMING
   - Some decisions took longer than optimal
   - Work on developing faster pattern recognition
   - Practice common spot decision trees

3. OPPONENT ANALYSIS
   - Missed opportunities to exploit opponent tendencies
   - Should take more detailed notes on betting patterns
   - Recommend studying population statistics

ACTIONABLE RECOMMENDATIONS:

- Next time in similar spot, consider betting larger for value
- Practice hand reading exercises to improve decision speed
- Review session notes to identify opponent patterns
- Study similar hands in training software

MISTAKE ANALYSIS:
The main suboptimal play was the river check instead of betting for value.
This represents a missed opportunity to extract additional value from weaker hands.

PRIORITY IMPROVEMENTS:
1. Value betting frequency (HIGH PRIORITY)
2. Hand reading accuracy (MEDIUM PRIORITY)  
3. Note-taking consistency (LOW PRIORITY)"""


def test_integration_comprehensive_analysis_components():
    """
    Integration test to verify that comprehensive analysis components 
    work together correctly.
    """
    # Test that the analysis service can handle comprehensive requests
    analysis_service = AIAnalysisService()
    
    # Verify service has the required methods
    assert hasattr(analysis_service, 'analyze_hand_comprehensive')
    assert hasattr(analysis_service, 'analyze_session_comprehensive')
    assert callable(analysis_service.analyze_hand_comprehensive)
    assert callable(analysis_service.analyze_session_comprehensive)
    
    # Verify service can determine analysis types
    assert hasattr(analysis_service, '_determine_analysis_type')
    assert hasattr(analysis_service, '_determine_session_analysis_type')
    
    # Test analysis type determination
    basic_type = analysis_service._determine_analysis_type('beginner', 'standard')
    assert basic_type == 'basic'
    
    advanced_type = analysis_service._determine_analysis_type('advanced', 'advanced')
    assert advanced_type == 'advanced'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])