"""
Hand history-related Pydantic schemas.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, validator
from .common import UUIDMixin, TimestampMixin, PaginationParams, DateRangeFilter, PlatformFilter, GameTypeFilter, PositionFilter


class DetailedAction(BaseModel):
    """Schema for individual poker actions."""
    player: str = Field(..., description="Player name")
    action: str = Field(..., pattern="^(fold|check|call|bet|raise|all-in)$", description="Action type")
    amount: Optional[Decimal] = Field(None, ge=0, description="Action amount")
    street: str = Field(..., pattern="^(preflop|flop|turn|river)$", description="Betting street")
    position: str = Field(..., description="Player position")
    time_used: Optional[int] = Field(None, ge=0, description="Time used for decision in seconds")
    timebank_used: Optional[int] = Field(None, ge=0, description="Timebank used in seconds")
    is_all_in: bool = Field(False, description="Whether action was all-in")
    stack_after: Decimal = Field(..., ge=0, description="Stack size after action")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['fold', 'check', 'call', 'bet', 'raise', 'all-in']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v
    
    @validator('street')
    def validate_street(cls, v):
        allowed_streets = ['preflop', 'flop', 'turn', 'river']
        if v not in allowed_streets:
            raise ValueError(f'Street must be one of: {", ".join(allowed_streets)}')
        return v


class HandResult(BaseModel):
    """Schema for hand result information."""
    result: str = Field(..., pattern="^(won|lost|folded|split)$", description="Hand outcome")
    amount_won: Optional[Decimal] = Field(None, description="Amount won (negative for losses)")
    showdown: bool = Field(False, description="Whether hand went to showdown")
    winning_hand: Optional[str] = Field(None, description="Winning hand description")
    
    @validator('result')
    def validate_result(cls, v):
        allowed_results = ['won', 'lost', 'folded', 'split']
        if v not in allowed_results:
            raise ValueError(f'Result must be one of: {", ".join(allowed_results)}')
        return v


class TournamentInfo(BaseModel):
    """Schema for tournament-specific information."""
    tournament_id: str = Field(..., description="Tournament identifier")
    tournament_name: Optional[str] = Field(None, description="Tournament name")
    buy_in: Optional[Decimal] = Field(None, ge=0, description="Tournament buy-in amount")
    level: Optional[int] = Field(None, ge=1, description="Tournament level")
    players_remaining: Optional[int] = Field(None, ge=1, description="Players remaining")
    total_players: Optional[int] = Field(None, ge=1, description="Total players started")
    prize_pool: Optional[Decimal] = Field(None, ge=0, description="Total prize pool")
    position_finished: Optional[int] = Field(None, ge=1, description="Final position if tournament ended")


class CashGameInfo(BaseModel):
    """Schema for cash game-specific information."""
    table_name: str = Field(..., description="Table identifier")
    table_type: Optional[str] = Field(None, description="Table type (regular, zoom, etc.)")
    max_players: Optional[int] = Field(None, ge=2, le=10, description="Maximum players at table")
    current_players: Optional[int] = Field(None, ge=2, description="Current players at table")


class PlayerStack(BaseModel):
    """Schema for player stack information."""
    player_name: str = Field(..., description="Player name")
    seat_number: int = Field(..., ge=1, le=10, description="Seat number")
    stack_size: Decimal = Field(..., ge=0, description="Stack size")
    is_sitting_out: bool = Field(False, description="Whether player is sitting out")


class TimebankInfo(BaseModel):
    """Schema for timebank usage information."""
    player_name: str = Field(..., description="Player name")
    time_used: int = Field(..., ge=0, description="Time used in seconds")
    timebank_used: int = Field(0, ge=0, description="Timebank used in seconds")
    timebank_remaining: Optional[int] = Field(None, ge=0, description="Timebank remaining")


class HandBase(BaseModel):
    """Base schema for poker hands."""
    hand_id: str = Field(..., description="Platform-specific hand ID")
    platform: str = Field(..., pattern="^(pokerstars|ggpoker)$", description="Poker platform")
    game_type: Optional[str] = Field(None, description="Game type")
    game_format: Optional[str] = Field(None, pattern="^(tournament|cash|sng)$", description="Game format")
    stakes: Optional[str] = Field(None, description="Stakes level")
    
    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ['pokerstars', 'ggpoker']
        if v not in allowed_platforms:
            raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        return v
    
    @validator('game_format')
    def validate_game_format(cls, v):
        if v is not None:
            allowed_formats = ['tournament', 'cash', 'sng']
            if v not in allowed_formats:
                raise ValueError(f'Game format must be one of: {", ".join(allowed_formats)}')
        return v


class HandCreate(HandBase):
    """Schema for creating a new hand record."""
    blinds: Optional[Dict[str, Decimal]] = Field(None, description="Blind structure")
    table_size: Optional[int] = Field(None, ge=2, le=10, description="Table size")
    date_played: Optional[datetime] = Field(None, description="When hand was played")
    player_cards: Optional[List[str]] = Field(None, description="Player hole cards")
    board_cards: Optional[List[str]] = Field(None, description="Community cards")
    position: Optional[str] = Field(None, description="Player position")
    seat_number: Optional[int] = Field(None, ge=1, le=10, description="Seat number")
    button_position: Optional[int] = Field(None, ge=1, le=10, description="Button position")
    actions: Optional[List[DetailedAction]] = Field(None, description="Hand actions")
    result: Optional[HandResult] = Field(None, description="Hand result")
    pot_size: Optional[Decimal] = Field(None, ge=0, description="Total pot size")
    rake: Optional[Decimal] = Field(None, ge=0, description="Rake amount")
    jackpot_contribution: Optional[Decimal] = Field(None, ge=0, description="Jackpot contribution")
    tournament_info: Optional[TournamentInfo] = Field(None, description="Tournament information")
    cash_game_info: Optional[CashGameInfo] = Field(None, description="Cash game information")
    player_stacks: Optional[List[PlayerStack]] = Field(None, description="Player stack information")
    timebank_info: Optional[List[TimebankInfo]] = Field(None, description="Timebank usage")
    hand_duration: Optional[int] = Field(None, ge=0, description="Hand duration in seconds")
    timezone: Optional[str] = Field(None, description="Timezone")
    currency: Optional[str] = Field(None, description="Currency")
    is_play_money: bool = Field(False, description="Whether play money game")
    raw_text: Optional[str] = Field(None, description="Original hand history text")


class HandUpdate(BaseModel):
    """Schema for updating hand information."""
    game_type: Optional[str] = Field(None, description="Updated game type")
    position: Optional[str] = Field(None, description="Updated position")
    result: Optional[HandResult] = Field(None, description="Updated result")
    is_play_money: Optional[bool] = Field(None, description="Updated play money status")


class HandResponse(HandBase, UUIDMixin, TimestampMixin):
    """Schema for hand response data."""
    user_id: str = Field(..., description="User ID who owns this hand")
    blinds: Optional[Dict[str, Any]] = Field(None, description="Blind structure")
    table_size: Optional[int] = Field(None, description="Table size")
    date_played: Optional[datetime] = Field(None, description="When hand was played")
    player_cards: Optional[List[str]] = Field(None, description="Player hole cards")
    board_cards: Optional[List[str]] = Field(None, description="Community cards")
    position: Optional[str] = Field(None, description="Player position")
    seat_number: Optional[int] = Field(None, description="Seat number")
    button_position: Optional[int] = Field(None, description="Button position")
    actions: Optional[Dict[str, Any]] = Field(None, description="Hand actions")
    result: Optional[str] = Field(None, description="Hand result")
    pot_size: Optional[Decimal] = Field(None, description="Total pot size")
    rake: Optional[Decimal] = Field(None, description="Rake amount")
    jackpot_contribution: Optional[Decimal] = Field(None, description="Jackpot contribution")
    tournament_info: Optional[Dict[str, Any]] = Field(None, description="Tournament information")
    cash_game_info: Optional[Dict[str, Any]] = Field(None, description="Cash game information")
    player_stacks: Optional[Dict[str, Any]] = Field(None, description="Player stack information")
    timebank_info: Optional[Dict[str, Any]] = Field(None, description="Timebank usage")
    hand_duration: Optional[int] = Field(None, description="Hand duration in seconds")
    timezone: Optional[str] = Field(None, description="Timezone")
    currency: Optional[str] = Field(None, description="Currency")
    is_play_money: bool = Field(False, description="Whether play money game")
    analysis_count: int = Field(0, description="Number of analyses for this hand")
    
    class Config:
        from_attributes = True


class HandListResponse(BaseModel):
    """Schema for paginated hand list response."""
    hands: List[HandResponse] = Field(..., description="List of hands")
    total: int = Field(..., ge=0, description="Total number of hands matching filters")
    skip: int = Field(..., ge=0, description="Number of records skipped")
    limit: int = Field(..., ge=1, description="Maximum records returned")
    has_more: bool = Field(..., description="Whether more records are available")


class HandUploadResponse(BaseModel):
    """Schema for hand history file upload response."""
    filename: str = Field(..., description="Uploaded filename")
    platform: str = Field(..., description="Detected platform")
    hands_processed: int = Field(..., ge=0, description="Number of hands successfully processed")
    hands_skipped: int = Field(0, ge=0, description="Number of hands skipped (duplicates)")
    errors: List[str] = Field(default_factory=list, description="Processing errors")
    processing_time: float = Field(..., ge=0, description="Processing time in seconds")
    file_size: int = Field(..., ge=0, description="File size in bytes")


class HandFilters(PaginationParams, DateRangeFilter, PlatformFilter, GameTypeFilter, PositionFilter):
    """Comprehensive filters for hand queries."""
    hand_id: Optional[str] = Field(None, description="Specific hand ID")
    min_pot_size: Optional[Decimal] = Field(None, ge=0, description="Minimum pot size")
    max_pot_size: Optional[Decimal] = Field(None, ge=0, description="Maximum pot size")
    is_play_money: Optional[bool] = Field(None, description="Filter by play money status")
    has_analysis: Optional[bool] = Field(None, description="Filter by analysis availability")
    tournament_only: Optional[bool] = Field(None, description="Tournament hands only")
    cash_only: Optional[bool] = Field(None, description="Cash game hands only")
    
    @validator('max_pot_size')
    def validate_pot_size_range(cls, v, values):
        if v and 'min_pot_size' in values and values['min_pot_size']:
            if v < values['min_pot_size']:
                raise ValueError('Maximum pot size must be greater than minimum pot size')
        return v


class HandBatchDeleteRequest(BaseModel):
    """Schema for batch hand deletion."""
    hand_ids: List[str] = Field(..., min_items=1, max_items=1000, description="List of hand IDs to delete")
    confirm_deletion: bool = Field(..., description="Confirmation of deletion intent")
    
    @validator('confirm_deletion')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError('Deletion must be explicitly confirmed')
        return v


class HandBatchDeleteResponse(BaseModel):
    """Schema for batch deletion response."""
    deleted_count: int = Field(..., ge=0, description="Number of hands successfully deleted")
    failed_deletions: List[str] = Field(default_factory=list, description="Hand IDs that failed to delete")
    errors: List[str] = Field(default_factory=list, description="Deletion errors")