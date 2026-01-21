"""
Analysis result model for storing AI-generated poker analysis.
"""
from decimal import Decimal
from typing import Dict, Any, List, Optional

from sqlalchemy import String, Text, ForeignKey, DECIMAL, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class AnalysisResult(Base, UUIDMixin, TimestampMixin):
    """Model for storing AI analysis results for poker hands."""
    
    __tablename__ = "analysis_results"
    
    # Foreign key to poker hand
    hand_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("poker_hands.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # AI provider information
    ai_provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="AI provider used: gemini, groq"
    )
    
    prompt_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        comment="Version of prompt template used"
    )
    
    # Analysis content
    analysis_text: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Full analysis text from AI provider"
    )
    
    strengths: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Identified strengths in play"
    )
    
    mistakes: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Identified mistakes or leaks"
    )
    
    recommendations: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        comment="Specific recommendations for improvement"
    )
    
    # Analysis metadata
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(3, 2),
        comment="AI confidence score (0.00-1.00)"
    )
    
    analysis_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Additional analysis data and metrics"
    )
    
    # Relationships
    hand = relationship("PokerHand", back_populates="analysis_results")
    
    # Indexes
    __table_args__ = (
        Index("idx_analysis_results_hand_provider", "hand_id", "ai_provider"),
    )
    
    def __repr__(self) -> str:
        return f"<AnalysisResult(id={self.id}, hand_id={self.hand_id}, provider={self.ai_provider})>"