"""
Statistics endpoints.
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.statistics import (
    StatisticsResponse,
    StatisticsSummary,
    StatisticsFilters,
    TrendData,
    StatisticsExportRequest,
    StatisticsExportResponse,
    StatisticsComparisonRequest,
    StatisticsComparisonResponse,
    BasicStatistics,
    AdvancedStatistics,
    SessionStatistics
)
from app.schemas.common import ErrorResponse
from app.models.user import User
from app.services.statistics_service import StatisticsService
from app.services.cache_service import get_stats_cache, StatisticsCacheService

router = APIRouter()


@router.get("/", response_model=StatisticsResponse, responses={400: {"model": ErrorResponse}})
async def get_statistics(
    filters: StatisticsFilters = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StatisticsResponse:
    """
    Get comprehensive poker statistics with dynamic filtering by multiple criteria.
    
    Calculates all poker statistics including:
    - Basic stats (VPIP, PFR, aggression factor, win rate)
    - Advanced stats (3-bet %, c-bet %, check-raise %, etc.)
    - Positional statistics
    - Tournament-specific metrics (if applicable)
    
    Supports dynamic filtering by multiple criteria:
    - Date range (start_date, end_date)
    - Platform (PokerStars, GGPoker)
    - Game type and format
    - Stakes level
    - Position
    - Minimum hands threshold
    - Tournament/cash game only
    - Play money inclusion/exclusion
    
    - **start_date**: Filter from this date
    - **end_date**: Filter until this date
    - **platform**: Filter by poker platform
    - **game_type**: Filter by game type
    - **game_format**: Filter by game format
    - **stakes**: Filter by stakes level
    - **position**: Filter by table position
    - **min_hands**: Minimum hands for statistical significance
    - **tournament_only**: Tournament hands only
    - **cash_only**: Cash game hands only
    - **play_money_only**: Play money hands only
    - **exclude_play_money**: Exclude play money hands
    """
    try:
        # Initialize statistics service with caching
        cache_service = await get_stats_cache()
        stats_service = StatisticsService(db, cache_service)
        
        # Calculate comprehensive statistics with filtering and caching
        return await stats_service.calculate_filtered_statistics(current_user.id, filters)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics: {str(e)}"
        )


@router.get("/summary", response_model=StatisticsSummary, responses={400: {"model": ErrorResponse}})
async def get_statistics_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StatisticsSummary:
    """
    Get quick statistics summary for dashboard with trend indicators.
    
    Returns essential statistics, recent session data, and trending metrics for dashboard display.
    """
    try:
        # Initialize statistics service
        stats_service = StatisticsService(db)
        
        # Calculate basic statistics for summary
        basic_stats = await stats_service.calculate_basic_statistics(current_user.id)
        
        # Calculate positional statistics to find best/worst positions
        positional_stats = await stats_service.calculate_positional_statistics(current_user.id)
        
        # Find best and worst positions by win rate
        best_position = None
        worst_position = None
        if positional_stats:
            best_pos = max(positional_stats, key=lambda x: x.win_rate)
            worst_pos = min(positional_stats, key=lambda x: x.win_rate)
            best_position = best_pos.position
            worst_position = worst_pos.position
        
        # Get recent session statistics
        recent_sessions = await stats_service.calculate_session_statistics(
            current_user.id,
            StatisticsFilters(
                start_date=datetime.now(timezone.utc) - timedelta(days=30)
            )
        )
        
        # Get trend analysis for key metrics
        trends = await stats_service.calculate_performance_trends(
            current_user.id,
            period="30d",
            metrics=["vpip", "pfr", "win_rate", "aggression_factor"]
        )
        
        # Categorize trending metrics
        trending_up = []
        trending_down = []
        
        for trend in trends:
            if trend.statistical_significance and trend.trend_strength > Decimal('0.3'):
                if trend.trend_direction == "up":
                    trending_up.append(trend.metric_name)
                elif trend.trend_direction == "down":
                    trending_down.append(trend.metric_name)
        
        return StatisticsSummary(
            total_hands=basic_stats.total_hands,
            win_rate=basic_stats.win_rate,
            vpip=basic_stats.vpip,
            pfr=basic_stats.pfr,
            recent_sessions=recent_sessions[:10],  # Last 10 sessions
            last_updated=datetime.now(timezone.utc),
            best_position=best_position,
            worst_position=worst_position,
            trending_up=trending_up,
            trending_down=trending_down
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics summary: {str(e)}"
        )


@router.get("/trends", response_model=List[TrendData], responses={400: {"model": ErrorResponse}})
async def get_performance_trends(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$", description="Time period for trends"),
    metrics: List[str] = Query(["vpip", "pfr", "win_rate"], description="Metrics to analyze trends for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TrendData]:
    """
    Get performance trends over time for specified metrics.
    
    Analyzes trends for specified metrics over the given time period with statistical significance testing.
    
    - **period**: Time period (7d, 30d, 90d, 1y)
    - **metrics**: List of metrics to analyze trends for (vpip, pfr, win_rate, aggression_factor, etc.)
    
    Returns trend analysis including:
    - Data points over time
    - Trend direction (up, down, stable)
    - Trend strength (0-1)
    - Statistical significance
    """
    try:
        # Initialize statistics service
        stats_service = StatisticsService(db)
        
        # Calculate performance trends
        trends = await stats_service.calculate_performance_trends(
            current_user.id,
            period=period,
            metrics=metrics
        )
        
        return trends
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating performance trends: {str(e)}"
        )


@router.get("/sessions", response_model=List[SessionStatistics], responses={400: {"model": ErrorResponse}})
async def get_session_statistics(
    filters: StatisticsFilters = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[SessionStatistics]:
    """
    Get session-based statistics grouped by date.
    
    Returns statistics for each playing session (grouped by date) with filtering support.
    
    - **start_date**: Filter sessions from this date
    - **end_date**: Filter sessions until this date
    - **platform**: Filter by poker platform
    - **game_type**: Filter by game type
    - **game_format**: Filter by game format
    """
    try:
        # Initialize statistics service
        stats_service = StatisticsService(db)
        
        # Calculate session statistics
        sessions = await stats_service.calculate_session_statistics(current_user.id, filters)
        
        return sessions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating session statistics: {str(e)}"
        )


@router.post("/export", response_model=StatisticsExportResponse, responses={400: {"model": ErrorResponse}})
async def export_statistics(
    request: StatisticsExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StatisticsExportResponse:
    """
    Export statistics in CSV, PDF, or JSON format.
    
    - **format**: Export format (csv, pdf, json)
    - **filters**: Filters to apply to exported data
    - **include_charts**: Include charts in export (PDF only)
    - **include_raw_data**: Include raw hand data
    - **sections**: Sections to include in export
    """
    # TODO: Implement statistics export
    from datetime import datetime, timedelta
    return StatisticsExportResponse(
        export_id="placeholder",
        download_url="/downloads/placeholder.csv",
        filename="statistics_export.csv",
        format=request.format,
        file_size=0,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc)
    )


@router.post("/compare", response_model=StatisticsComparisonResponse, responses={400: {"model": ErrorResponse}})
async def compare_statistics(
    request: StatisticsComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StatisticsComparisonResponse:
    """
    Compare statistics between two time periods.
    
    - **base_period**: Base period filters for comparison
    - **comparison_period**: Comparison period filters
    - **metrics**: Metrics to compare between periods
    """
    # TODO: Implement statistics comparison
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Statistics comparison not implemented"
    )