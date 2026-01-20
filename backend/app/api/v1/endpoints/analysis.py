"""
Analysis API endpoints.

Provides endpoints for AI-powered poker analysis using YAML prompts
with flexible AI provider selection (Gemini, Groq).
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ....core.database import get_db
from ....services.ai_analysis import get_ai_analysis_service, AIProvider, AnalysisResult
from ....services.prompt_manager import get_prompt_manager
from ....schemas.analysis import (
    HandAnalysisRequest,
    SessionAnalysisRequest,
    AnalysisResponse,
    SessionAnalysisResponse,
    AnalysisJobResponse
)
from ....schemas.hand import HandResponse
from ....api.deps import get_current_user
from ....models.user import User
from ....models.hand import PokerHand
from ....models.analysis import AnalysisResult as AnalysisModel

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/prompts/categories", response_model=Dict[str, List[str]])
async def get_prompt_categories():
    """
    Get available prompt categories and types.
    
    Returns all available analysis categories and their types
    from the YAML prompt system.
    """
    try:
        ai_service = get_ai_analysis_service()
        return ai_service.get_available_analysis_types()
    except Exception as e:
        logger.error(f"Error getting prompt categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt categories"
        )


@router.get("/prompts/info")
async def get_prompt_info():
    """
    Get information about the prompt management system.
    
    Returns metadata about loaded prompts, categories, and system status.
    """
    try:
        prompt_manager = get_prompt_manager()
        return prompt_manager.get_prompt_info()
    except Exception as e:
        logger.error(f"Error getting prompt info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt information"
        )


@router.post("/prompts/reload")
async def reload_prompts(current_user: User = Depends(get_current_user)):
    """
    Reload YAML prompts from files.
    
    Useful for development and updating prompts without restarting the service.
    Requires authentication.
    """
    try:
        prompt_manager = get_prompt_manager()
        success = prompt_manager.reload_prompts()
        
        if success:
            return {
                "message": "Prompts reloaded successfully",
                "categories_loaded": len(prompt_manager.get_available_categories())
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reload prompts"
            )
    except Exception as e:
        logger.error(f"Error reloading prompts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload prompts"
        )


@router.post("/hand/{hand_id}/analyze", response_model=AnalysisJobResponse)
async def analyze_hand(
    hand_id: str,
    request: HandAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a single poker hand using AI.
    
    Creates an AI analysis job for the specified hand using the selected
    AI provider and analysis depth.
    """
    try:
        # Verify hand exists and belongs to user
        # This would typically query the database
        # For now, we'll create a mock response
        
        ai_service = get_ai_analysis_service()
        
        # Validate the analysis request
        if not ai_service.validate_analysis_request("hand_analysis", request.analysis_depth):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid analysis type: {request.analysis_depth}"
            )
        
        # In a real implementation, this would:
        # 1. Fetch the hand from database
        # 2. Get user's API key for the selected provider
        # 3. Queue the analysis job
        # 4. Return job ID for status tracking
        
        return AnalysisJobResponse(
            analysis_id=f"analysis_{hand_id}_{request.ai_provider}",
            status="pending",
            progress=0,
            message=f"Comprehensive analysis queued for hand {hand_id} using {request.ai_provider}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating hand analysis job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis job"
        )


@router.post("/hand/{hand_id}/analyze-comprehensive", response_model=Dict[str, Any])
async def analyze_hand_comprehensive(
    hand_id: str,
    request: HandAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive hand-by-hand analysis with adaptive depth.
    
    Implements requirements 7.1, 7.6, 7.8:
    - Strategic advice for each decision point
    - Hand-by-hand breakdowns with specific recommendations
    - Adaptive analysis depth based on user experience level
    """
    try:
        # Convert string to AIProvider enum
        try:
            ai_provider = AIProvider(request.ai_provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.ai_provider}"
            )
        
        # For development, we'll use mock data
        # In production, this would fetch from database
        from ...schemas.hand import HandResponse
        from datetime import datetime
        mock_hand = HandResponse(
            id=hand_id,
            hand_id=hand_id,
            platform="pokerstars",
            game_type="No Limit Hold'em",
            stakes="$0.25/$0.50",
            position="Button",
            player_cards=["As", "Kh"],
            board_cards=["Qh", "Jc", "9s"],
            actions={
                "preflop": [
                    {"player": "Hero", "action": "raise", "amount": 1.50, "street": "preflop"},
                    {"player": "Villain", "action": "call", "amount": 1.50, "street": "preflop"}
                ],
                "flop": [
                    {"player": "Hero", "action": "bet", "amount": 2.25, "street": "flop"}
                ]
            },
            result="Won $4.50",
            pot_size=4.50,
            user_id=current_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        ai_service = get_ai_analysis_service()
        
        # Get user's API key (empty string will use dev keys if available)
        api_key = ""  # In production, this would come from user settings
        
        # Perform comprehensive analysis
        result = await ai_service.analyze_hand_comprehensive(
            hand=mock_hand,
            provider=ai_provider,
            api_key=api_key,
            experience_level="intermediate",  # Would come from user profile
            analysis_depth=request.analysis_depth,
            focus_areas=request.focus_areas
        )
        
        if result.success:
            return {
                "hand_id": hand_id,
                "analysis_type": "comprehensive",
                "provider": result.provider.value,
                "content": result.content,
                "structured_insights": result.metadata.get('structured_insights', {}),
                "decision_points": result.metadata.get('decision_points', []),
                "key_decisions": result.metadata.get('key_decisions', ''),
                "analysis_depth": request.analysis_depth,
                "focus_areas": request.focus_areas or [],
                "usage": result.usage,
                "metadata": result.metadata
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Comprehensive analysis failed: {result.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive hand analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform comprehensive analysis"
        )


@router.post("/session/analyze", response_model=AnalysisJobResponse)
async def analyze_session(
    request: SessionAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze a poker session with multiple hands.
    
    Creates an AI analysis job for the specified hands using session
    analysis prompts and the selected AI provider.
    """
    try:
        ai_service = get_ai_analysis_service()
        
        # Validate the analysis request
        if not ai_service.validate_analysis_request("session_analysis", request.analysis_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid session analysis type: {request.analysis_type}"
            )
        
        # Validate hand count
        if len(request.hand_ids) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many hands for session analysis (max 1000)"
            )
        
        # In a real implementation, this would:
        # 1. Fetch all hands from database
        # 2. Verify all hands belong to the user
        # 3. Calculate session statistics
        # 4. Queue the session analysis job
        # 5. Return job ID for status tracking
        
        return AnalysisJobResponse(
            analysis_id=f"session_{len(request.hand_ids)}_{request.ai_provider}",
            status="pending",
            progress=0,
            message=f"Comprehensive session analysis queued for {len(request.hand_ids)} hands using {request.ai_provider}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating session analysis job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session analysis job"
        )


@router.post("/session/analyze-comprehensive", response_model=Dict[str, Any])
async def analyze_session_comprehensive(
    request: SessionAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive session analysis with individual hand breakdowns.
    
    Implements requirements 7.1, 7.6, 7.8:
    - Strategic advice for session patterns and individual decisions
    - Session-level breakdowns with specific recommendations
    - Adaptive analysis depth based on user experience level
    """
    try:
        # Convert string to AIProvider enum
        try:
            ai_provider = AIProvider(request.ai_provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {request.ai_provider}"
            )
        
        # Validate hand count
        if len(request.hand_ids) > 100:  # Limit for comprehensive analysis
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many hands for comprehensive analysis (max 100)"
            )
        
        # For development, create mock session data
        from ...schemas.hand import HandResponse
        from datetime import datetime
        mock_hands = []
        for i, hand_id in enumerate(request.hand_ids[:5]):  # Limit to 5 for demo
            mock_hands.append(HandResponse(
                id=hand_id,
                hand_id=hand_id,
                platform="pokerstars",
                game_type="No Limit Hold'em",
                stakes="$0.25/$0.50",
                position=["UTG", "MP", "CO", "BTN", "SB"][i % 5],
                player_cards=["As Kh", "Qd Jc", "9h 8s", "Ah Kc", "Td 9d"][i % 5].split(),
                board_cards=[],
                actions={"preflop": [{"player": "Hero", "action": "fold", "street": "preflop"}]},
                result="Lost $0.50",
                pot_size=1.0,
                user_id=current_user.id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ))
        
        # Mock session statistics
        mock_session_stats = {
            "vpip": 22.5,
            "pfr": 18.0,
            "aggression_factor": 2.1,
            "win_rate": 3.5,
            "three_bet_percentage": 8.5,
            "cbet_flop": 65.0,
            "hands_played": len(request.hand_ids)
        }
        
        ai_service = get_ai_analysis_service()
        
        # Get user's API key (empty string will use dev keys if available)
        api_key = ""  # In production, this would come from user settings
        
        # Perform comprehensive session analysis
        result = await ai_service.analyze_session_comprehensive(
            hands=mock_hands,
            session_stats=mock_session_stats,
            provider=ai_provider,
            api_key=api_key,
            analysis_type=request.analysis_type,
            experience_level="intermediate",  # Would come from user profile
            include_individual_hands=True
        )
        
        if result.success:
            return {
                "session_id": f"session_{len(request.hand_ids)}",
                "analysis_type": "comprehensive",
                "provider": result.provider.value,
                "hands_analyzed": len(mock_hands),
                "content": result.content,
                "structured_insights": result.metadata.get('structured_insights', {}),
                "session_stats": mock_session_stats,
                "individual_hands": result.metadata.get('individual_hand_summaries', []),
                "improvement_priorities": result.metadata.get('improvement_priorities', []),
                "leak_analysis": result.metadata.get('leak_analysis', []),
                "strength_analysis": result.metadata.get('strength_analysis', []),
                "usage": result.usage,
                "metadata": result.metadata
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Comprehensive session analysis failed: {result.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in comprehensive session analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform comprehensive session analysis"
        )


@router.get("/educational/{concept}", response_model=Dict[str, Any])
async def get_educational_content(
    concept: str,
    provider: str = "gemini",
    api_key: str = "",
    experience_level: str = "intermediate",
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get educational content about a poker concept.
    
    Uses AI to generate educational explanations about poker concepts,
    statistics, and strategies tailored to the user's experience level.
    """
    try:
        # Convert string to AIProvider enum
        try:
            ai_provider = AIProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key is required"
            )
        
        ai_service = get_ai_analysis_service()
        
        result = await ai_service.get_educational_content(
            concept=concept,
            provider=ai_provider,
            api_key=api_key,
            experience_level=experience_level,
            context=context
        )
        
        if result.success:
            return {
                "concept": concept,
                "content": result.content,
                "provider": result.provider.value,
                "experience_level": experience_level,
                "usage": result.usage,
                "metadata": result.metadata
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate educational content: {result.error}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating educational content for {concept}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate educational content"
        )


@router.get("/providers", response_model=Dict[str, Any])
async def get_available_providers():
    """
    Get list of available AI providers with their capabilities.
    
    Returns the AI providers that can be used for analysis along with
    their capabilities, default models, and rate limits.
    """
    try:
        ai_service = get_ai_analysis_service()
        providers = ai_service.get_available_providers()
        
        provider_info = {}
        for provider in providers:
            capabilities = ai_service.get_provider_capabilities(provider)
            provider_info[provider.value] = {
                "name": provider.value,
                "capabilities": capabilities,
                "default_model": ai_service.get_default_models().get(provider, "unknown")
            }
        
        return {
            "providers": provider_info,
            "total_count": len(providers)
        }
    except Exception as e:
        logger.error(f"Error getting available providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available providers"
        )


@router.post("/providers/{provider}/validate-key")
async def validate_api_key(
    provider: str,
    api_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate an API key for a specific AI provider.
    
    Tests the API key by making a simple request to verify it works.
    """
    try:
        # Convert string to AIProvider enum
        try:
            ai_provider = AIProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        ai_service = get_ai_analysis_service()
        is_valid = await ai_service.validate_api_key(ai_provider, api_key)
        
        return {
            "provider": provider,
            "is_valid": is_valid,
            "message": "API key is valid" if is_valid else "API key is invalid or expired"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate API key"
        )


@router.post("/validate-prompt")
async def validate_prompt_structure(
    category: str,
    prompt_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Validate a prompt structure.
    
    Checks if a specific prompt category and type exists and has
    the correct structure for analysis.
    """
    try:
        prompt_manager = get_prompt_manager()
        is_valid = prompt_manager.validate_prompt_structure(category, prompt_type)
        
        return {
            "category": category,
            "prompt_type": prompt_type,
            "is_valid": is_valid,
            "available_types": prompt_manager.get_available_types(category) if category in prompt_manager.get_available_categories() else []
        }
        
    except Exception as e:
        logger.error(f"Error validating prompt {category}.{prompt_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate prompt structure"
        )


@router.post("/test/ai-integration")
async def test_ai_integration(
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Test AI provider integration with a simple request.
    
    Development endpoint to test AI provider connectivity and response quality.
    """
    try:
        # Convert string to AIProvider enum
        try:
            ai_provider = AIProvider(provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {provider}"
            )
        
        ai_service = get_ai_analysis_service()
        
        # Test with a simple educational content request
        result = await ai_service.get_educational_content(
            concept="VPIP",
            provider=ai_provider,
            api_key=api_key,
            experience_level="beginner",
            context="Testing AI integration",
            model=model,
            temperature=0.7,
            max_tokens=500
        )
        
        return {
            "provider": provider,
            "model": model or "default",
            "success": result.success,
            "content_length": len(result.content) if result.content else 0,
            "usage": result.usage,
            "error": result.error,
            "metadata": result.metadata,
            "test_timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing AI integration for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test AI integration"
        )


@router.post("/test/format-prompt")
async def test_format_prompt(
    category: str,
    prompt_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Test prompt formatting with sample data.
    
    Development endpoint to test prompt formatting with mock data.
    Useful for validating prompt templates.
    """
    try:
        prompt_manager = get_prompt_manager()
        
        # Sample data for testing
        sample_data = {
            'experience_level': 'intermediate',
            'platform': 'PokerStars',
            'game_type': 'No Limit Hold\'em',
            'stakes': '$0.25/$0.50',
            'position': 'Button',
            'player_cards': 'As Kh',
            'board_cards': 'Qh Jc 9s',
            'actions': 'Hero raises $1.50, Villain calls',
            'result': 'Won $3.25',
            'pot_size': '$3.25',
            'concept_name': 'VPIP',
            'context': 'Understanding basic poker statistics',
            'session_length': 100,
            'time_duration': '2 hours',
            'vpip': 25.5,
            'pfr': 18.2,
            'aggression_factor': 2.1,
            'win_rate': 5.5,
            'three_bet_pct': 8.0,
            'cbet_pct': 65.0,
            'significant_hands_count': 5,
            'session_results': 'Winning session: +5.5 BB/100',
            'session_patterns': 'Playing tight-aggressive style'
        }
        
        formatted = prompt_manager.format_prompt(category, prompt_type, **sample_data)
        
        if formatted:
            return {
                "category": category,
                "prompt_type": prompt_type,
                "formatted_successfully": True,
                "system_prompt_length": len(formatted['system']),
                "user_prompt_length": len(formatted['user']),
                "system_preview": formatted['system'][:200] + "..." if len(formatted['system']) > 200 else formatted['system'],
                "user_preview": formatted['user'][:200] + "..." if len(formatted['user']) > 200 else formatted['user'],
                "metadata": formatted.get('metadata', {})
            }
        else:
            return {
                "category": category,
                "prompt_type": prompt_type,
                "formatted_successfully": False,
                "error": "Failed to format prompt"
            }
            
    except Exception as e:
        logger.error(f"Error testing prompt format {category}.{prompt_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test prompt formatting"
        )