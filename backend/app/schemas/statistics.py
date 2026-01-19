"""
Statistics-related Pydantic schemas.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from .common import DateRangeFilter, PlatformFilter, GameTypeFilter, PositionFilter


class StatisticsFilters(DateRangeFilter, PlatformFilter, GameTypeFilter, PositionFilter):
    """Comprehensive filters for statistics queries."""
    min_hands: Optional[int] = Field(None, ge=1, description="Minimum number of hands for statistics")
    stakes_filter: Optional[List[str]] = Field(None, description="Specific stakes to include")
    tournament_only: Optional[bool] = Field(None, description="Tournament hands only")
    cash_only: Optional[bool] = Field(None, description="Cash game hands only")
    play_money_only: Optional[bool] = Field(None, description="Play money hands only")
    exclude_play_money: Optional[bool] = Field(None, description="Exclude play money hands")


class BasicStatistics(BaseModel):
    """Schema for basic poker statistics."""
    total_hands: int = Field(..., ge=0, description="Total number of hands")
    vpip: Decimal = Field(..., ge=0, le=100, description="Voluntarily Put In Pot percentage")
    pfr: Decimal = Field(..., ge=0, le=100, description="Pre-Flop Raise percentage")
    aggression_factor: Decimal = Field(..., ge=0, description="Aggression factor")
    win_rate: Decimal = Field(..., description="Win rate (bb/100 or ROI%)")
    
    # Basic preflop stats
    fold_to_steal: Optional[Decimal] = Field(None, ge=0, le=100, description="Fold to steal percentage")
    attempt_to_steal: Optional[Decimal] = Field(None, ge=0, le=100, description="Attempt to steal percentage")
    
    # Basic postflop stats
    went_to_showdown: Optional[Decimal] = Field(None, ge=0, le=100, description="Went to showdown percentage")
    won_at_showdown: Optional[Decimal] = Field(None, ge=0, le=100, description="Won at showdown percentage")


class AdvancedStatistics(BaseModel):
    """Schema for advanced poker statistics."""
    # Advanced preflop stats
    three_bet_percentage: Decimal = Field(..., ge=0, le=100, description="3-bet percentage")
    fold_to_three_bet: Decimal = Field(..., ge=0, le=100, description="Fold to 3-bet percentage")
    four_bet_percentage: Decimal = Field(..., ge=0, le=100, description="4-bet percentage")
    fold_to_four_bet: Decimal = Field(..., ge=0, le=100, description="Fold to 4-bet percentage")
    cold_call_percentage: Decimal = Field(..., ge=0, le=100, description="Cold call percentage")
    isolation_raise: Decimal = Field(..., ge=0, le=100, description="Isolation raise percentage")
    
    # Advanced postflop stats
    c_bet_flop: Decimal = Field(..., ge=0, le=100, description="Continuation bet flop percentage")
    c_bet_turn: Decimal = Field(..., ge=0, le=100, description="Continuation bet turn percentage")
    c_bet_river: Decimal = Field(..., ge=0, le=100, description="Continuation bet river percentage")
    fold_to_c_bet_flop: Decimal = Field(..., ge=0, le=100, description="Fold to c-bet flop percentage")
    fold_to_c_bet_turn: Decimal = Field(..., ge=0, le=100, description="Fold to c-bet turn percentage")
    fold_to_c_bet_river: Decimal = Field(..., ge=0, le=100, description="Fold to c-bet river percentage")
    check_raise_flop: Decimal = Field(..., ge=0, le=100, description="Check-raise flop percentage")
    check_raise_turn: Decimal = Field(..., ge=0, le=100, description="Check-raise turn percentage")
    check_raise_river: Decimal = Field(..., ge=0, le=100, description="Check-raise river percentage")
    
    # Advanced metrics
    red_line_winnings: Decimal = Field(..., description="Non-showdown winnings")
    blue_line_winnings: Decimal = Field(..., description="Showdown winnings")
    expected_value: Decimal = Field(..., description="Expected value")
    variance: Decimal = Field(..., ge=0, description="Variance")
    standard_deviations: Decimal = Field(..., description="Standard deviations from expected")


class PositionalStatistics(BaseModel):
    """Schema for position-based statistics."""
    position: str = Field(..., description="Table position")
    hands_played: int = Field(..., ge=0, description="Hands played from this position")
    vpip: Decimal = Field(..., ge=0, le=100, description="VPIP from this position")
    pfr: Decimal = Field(..., ge=0, le=100, description="PFR from this position")
    win_rate: Decimal = Field(..., description="Win rate from this position")
    aggression_factor: Decimal = Field(..., ge=0, description="Aggression factor from this position")
    three_bet_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="3-bet % from position")
    fold_to_three_bet: Optional[Decimal] = Field(None, ge=0, le=100, description="Fold to 3-bet % from position")


class TournamentStatistics(BaseModel):
    """Schema for tournament-specific statistics."""
    tournaments_played: int = Field(..., ge=0, description="Total tournaments played")
    tournaments_cashed: int = Field(..., ge=0, description="Tournaments cashed")
    cash_percentage: Decimal = Field(..., ge=0, le=100, description="Cash percentage")
    average_finish: Decimal = Field(..., ge=0, description="Average finish position")
    roi: Decimal = Field(..., description="Return on investment percentage")
    total_buy_ins: Decimal = Field(..., ge=0, description="Total buy-ins spent")
    total_winnings: Decimal = Field(..., ge=0, description="Total winnings")
    profit: Decimal = Field(..., description="Total profit/loss")
    
    # ICM and bubble stats
    bubble_factor: Optional[Decimal] = Field(None, ge=0, description="Bubble factor")
    icm_pressure_spots: Optional[int] = Field(None, ge=0, description="ICM pressure situations")
    final_table_appearances: Optional[int] = Field(None, ge=0, description="Final table appearances")


class SessionStatistics(BaseModel):
    """Schema for session-based statistics."""
    session_date: datetime = Field(..., description="Session date")
    hands_played: int = Field(..., ge=0, description="Hands played in session")
    duration_minutes: int = Field(..., ge=0, description="Session duration in minutes")
    win_rate: Decimal = Field(..., description="Session win rate")
    vpip: Decimal = Field(..., ge=0, le=100, description="Session VPIP")
    pfr: Decimal = Field(..., ge=0, le=100, description="Session PFR")
    aggression_factor: Decimal = Field(..., ge=0, description="Session aggression factor")
    biggest_win: Decimal = Field(..., description="Biggest winning hand")
    biggest_loss: Decimal = Field(..., description="Biggest losing hand")
    net_result: Decimal = Field(..., description="Net session result")


class TrendDataPoint(BaseModel):
    """Schema for individual trend data points."""
    date: datetime = Field(..., description="Data point date")
    value: Decimal = Field(..., description="Metric value")
    hands_sample: int = Field(..., ge=0, description="Number of hands in sample")
    confidence: Optional[Decimal] = Field(None, ge=0, le=1, description="Confidence level")


class TrendData(BaseModel):
    """Schema for trend analysis data."""
    metric_name: str = Field(..., description="Name of the metric")
    time_period: str = Field(..., description="Time period for trend")
    data_points: List[TrendDataPoint] = Field(..., description="Trend data points")
    trend_direction: str = Field(..., pattern="^(up|down|stable)$", description="Overall trend direction")
    trend_strength: Decimal = Field(..., ge=0, le=1, description="Strength of trend (0-1)")
    statistical_significance: bool = Field(..., description="Whether trend is statistically significant")
    
    @validator('trend_direction')
    def validate_trend_direction(cls, v):
        allowed_directions = ['up', 'down', 'stable']
        if v not in allowed_directions:
            raise ValueError(f'Trend direction must be one of: {", ".join(allowed_directions)}')
        return v


class StatisticsResponse(BaseModel):
    """Schema for comprehensive statistics response."""
    basic_stats: BasicStatistics = Field(..., description="Basic poker statistics")
    advanced_stats: AdvancedStatistics = Field(..., description="Advanced poker statistics")
    positional_stats: List[PositionalStatistics] = Field(..., description="Position-based statistics")
    tournament_stats: Optional[TournamentStatistics] = Field(None, description="Tournament statistics")
    
    # Metadata
    filters_applied: StatisticsFilters = Field(..., description="Filters used for calculation")
    calculation_date: datetime = Field(..., description="When statistics were calculated")
    cache_expires: datetime = Field(..., description="When cached statistics expire")
    sample_size: int = Field(..., ge=0, description="Total hands in sample")
    confidence_level: Decimal = Field(..., ge=0, le=1, description="Statistical confidence level")


class StatisticsSummary(BaseModel):
    """Schema for quick statistics summary."""
    total_hands: int = Field(..., ge=0, description="Total hands played")
    win_rate: Decimal = Field(..., description="Overall win rate")
    vpip: Decimal = Field(..., ge=0, le=100, description="Overall VPIP")
    pfr: Decimal = Field(..., ge=0, le=100, description="Overall PFR")
    recent_sessions: List[SessionStatistics] = Field(..., description="Recent session data")
    last_updated: datetime = Field(..., description="Last update time")
    
    # Quick insights
    best_position: Optional[str] = Field(None, description="Most profitable position")
    worst_position: Optional[str] = Field(None, description="Least profitable position")
    trending_up: List[str] = Field(default_factory=list, description="Metrics trending upward")
    trending_down: List[str] = Field(default_factory=list, description="Metrics trending downward")


class StatisticsExportRequest(BaseModel):
    """Schema for statistics export request."""
    format: str = Field(..., pattern="^(csv|pdf|json)$", description="Export format")
    filters: StatisticsFilters = Field(..., description="Filters to apply")
    include_charts: bool = Field(True, description="Include charts in export (PDF only)")
    include_raw_data: bool = Field(False, description="Include raw hand data")
    sections: List[str] = Field(
        default_factory=lambda: ["basic", "advanced", "positional", "trends"],
        description="Sections to include in export"
    )
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['csv', 'pdf', 'json']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v
    
    @validator('sections')
    def validate_sections(cls, v):
        allowed_sections = ['basic', 'advanced', 'positional', 'tournament', 'trends', 'sessions']
        for section in v:
            if section not in allowed_sections:
                raise ValueError(f'Section must be one of: {", ".join(allowed_sections)}')
        return v


class StatisticsExportResponse(BaseModel):
    """Schema for statistics export response."""
    export_id: str = Field(..., description="Export job ID")
    download_url: str = Field(..., description="Download URL for exported file")
    filename: str = Field(..., description="Generated filename")
    format: str = Field(..., description="Export format")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    expires_at: datetime = Field(..., description="Download link expiration")
    created_at: datetime = Field(..., description="Export creation time")


class StatisticsComparisonRequest(BaseModel):
    """Schema for comparing statistics between periods."""
    base_period: StatisticsFilters = Field(..., description="Base period for comparison")
    comparison_period: StatisticsFilters = Field(..., description="Period to compare against")
    metrics: List[str] = Field(
        default_factory=lambda: ["vpip", "pfr", "win_rate", "aggression_factor"],
        description="Metrics to compare"
    )


class StatisticsComparisonResponse(BaseModel):
    """Schema for statistics comparison response."""
    base_period_stats: StatisticsResponse = Field(..., description="Base period statistics")
    comparison_period_stats: StatisticsResponse = Field(..., description="Comparison period statistics")
    differences: Dict[str, Decimal] = Field(..., description="Metric differences")
    significant_changes: List[Dict[str, Any]] = Field(..., description="Statistically significant changes")
    improvement_areas: List[str] = Field(..., description="Areas showing improvement")
    decline_areas: List[str] = Field(..., description="Areas showing decline")
    recommendations: List[str] = Field(..., description="Recommendations based on comparison")