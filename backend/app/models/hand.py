"""
Poker hand model for storing comprehensive hand history data.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    String, Text, Integer, Boolean, DateTime, 
    DECIMAL, ForeignKey, UniqueConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class PokerHand(Base, UUIDMixin, TimestampMixin):
    """Comprehensive poker hand model supporting multiple platforms."""
    
    __tablename__ = "poker_hands"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Hand identification
    hand_id: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        comment="Platform-specific hand ID"
    )
    
    platform: Mapped[str] = mapped_column(
        String(20), 
        nullable=False,
        comment="Poker platform: pokerstars, ggpoker"
    )
    
    # Game information
    game_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="Game type: Hold'em, Omaha, etc."
    )
    
    game_format: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Game format: tournament, cash, sng"
    )
    
    stakes: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Stakes level: $0.50/$1.00, etc."
    )
    
    # Blind structure
    blinds: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Blind structure: {small: 0.5, big: 1.0, ante: 0.1}"
    )
    
    table_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Number of seats at table"
    )
    
    # Timing information
    date_played: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        index=True,
        comment="When the hand was played"
    )
    
    # Cards and position
    player_cards: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Player's hole cards"
    )
    
    board_cards: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Community cards"
    )
    
    position: Mapped[Optional[str]] = mapped_column(
        String(20),
        index=True,
        comment="Player position: UTG, MP, CO, BTN, SB, BB"
    )
    
    seat_number: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Seat number at table"
    )
    
    button_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Button seat number"
    )
    
    # Actions and results
    actions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Detailed action sequence for all streets"
    )
    
    result: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="Hand result: won, lost, folded"
    )
    
    # Financial information
    pot_size: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 2),
        comment="Total pot size"
    )
    
    rake: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 2),
        comment="Rake taken by house"
    )
    
    jackpot_contribution: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 2),
        comment="Jackpot contribution amount"
    )
    
    # Tournament and cash game specific data
    tournament_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Tournament ID, level, blinds progression, etc."
    )
    
    cash_game_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Cash game table information"
    )
    
    # Player information
    player_stacks: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="All player stack sizes and positions"
    )
    
    timebank_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Time usage and timebank information"
    )
    
    hand_duration: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Hand duration in seconds"
    )
    
    # Metadata
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Timezone when hand was played"
    )
    
    currency: Mapped[Optional[str]] = mapped_column(
        String(10),
        comment="Currency used in the game"
    )
    
    is_play_money: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a play money game"
    )
    
    # Raw hand history text for reference
    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Original hand history text"
    )
    
    # Relationships
    user = relationship("User", back_populates="poker_hands")
    analysis_results = relationship("AnalysisResult", back_populates="hand", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "hand_id", "platform", name="uq_user_hand_platform"),
        Index("idx_poker_hands_user_platform_date", "user_id", "platform", "date_played"),
        Index("idx_poker_hands_game_format", "game_format"),
        Index("idx_poker_hands_stakes", "stakes"),
        Index("idx_poker_hands_position", "position"),
    )
    
    def __repr__(self) -> str:
        return f"<PokerHand(id={self.id}, hand_id={self.hand_id}, platform={self.platform})>"