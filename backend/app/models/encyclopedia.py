"""
Encyclopedia database models for AI-powered content management.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base, UUIDMixin, TimestampMixin


class EncyclopediaStatus(str, Enum):
    """Status values for encyclopedia entries."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AIProvider(str, Enum):
    """AI providers for content generation."""
    GROQ = "groq"
    GEMINI = "gemini"


class EncyclopediaEntry(Base, UUIDMixin, TimestampMixin):
    """
    Encyclopedia entry model for AI-generated poker content.
    
    Stores comprehensive poker knowledge entries with AI-powered content
    generation, conversation history, and inter-entry linking.
    """
    __tablename__ = "encyclopedia_entries"
    
    # Basic entry information
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique title for the encyclopedia entry"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Main content of the encyclopedia entry"
    )
    
    # Status and workflow
    status: Mapped[EncyclopediaStatus] = mapped_column(
        String(20),
        nullable=False,
        default=EncyclopediaStatus.DRAFT,
        index=True,
        comment="Current status of the entry (draft, published, archived)"
    )
    
    # AI generation metadata
    ai_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="AI provider used to generate the content (groq, gemini)"
    )
    
    # User management
    created_by: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the entry"
    )
    
    approved_by: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id"),
        nullable=True,
        comment="User who approved the entry for publication"
    )
    
    # Publication timestamp
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the entry was published"
    )
    
    # Relationships
    conversations = relationship(
        "EncyclopediaConversation",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="EncyclopediaConversation.created_at"
    )
    
    source_links = relationship(
        "EncyclopediaLink",
        foreign_keys="EncyclopediaLink.source_entry_id",
        back_populates="source_entry",
        cascade="all, delete-orphan"
    )
    
    target_links = relationship(
        "EncyclopediaLink",
        foreign_keys="EncyclopediaLink.target_entry_id",
        back_populates="target_entry"
    )
    
    # User relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self) -> str:
        return f"<EncyclopediaEntry(id={self.id}, title='{self.title}', status='{self.status}')>"


class EncyclopediaConversation(Base, UUIDMixin, TimestampMixin):
    """
    Conversation history for encyclopedia entry generation and refinement.
    
    Tracks the iterative AI conversation process used to generate and
    refine encyclopedia content.
    """
    __tablename__ = "encyclopedia_conversations"
    
    # Entry relationship
    entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("encyclopedia_entries.id"),
        nullable=False,
        index=True,
        comment="Encyclopedia entry this conversation belongs to"
    )
    
    # Conversation content
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User prompt or instruction sent to AI"
    )
    
    response: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="AI response to the prompt"
    )
    
    # AI metadata
    ai_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="AI provider used for this conversation turn"
    )
    
    # Additional metadata
    conversation_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata like model version, temperature, etc."
    )
    
    # Relationships
    entry = relationship("EncyclopediaEntry", back_populates="conversations")
    
    def __repr__(self) -> str:
        return f"<EncyclopediaConversation(id={self.id}, entry_id={self.entry_id}, provider='{self.ai_provider}')>"


class EncyclopediaLink(Base, UUIDMixin, TimestampMixin):
    """
    Inter-entry links for encyclopedia navigation.
    
    Stores Wikipedia-style hyperlinks between related encyclopedia entries
    with context and anchor text information.
    """
    __tablename__ = "encyclopedia_links"
    
    # Source and target entries
    source_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("encyclopedia_entries.id"),
        nullable=False,
        index=True,
        comment="Entry that contains the link"
    )
    
    target_entry_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("encyclopedia_entries.id"),
        nullable=False,
        index=True,
        comment="Entry that the link points to"
    )
    
    # Link details
    anchor_text: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Text that appears as the clickable link"
    )
    
    context: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Surrounding context where the link appears"
    )
    
    # Relationships
    source_entry = relationship(
        "EncyclopediaEntry",
        foreign_keys=[source_entry_id],
        back_populates="source_links"
    )
    
    target_entry = relationship(
        "EncyclopediaEntry",
        foreign_keys=[target_entry_id],
        back_populates="target_links"
    )
    
    def __repr__(self) -> str:
        return f"<EncyclopediaLink(id={self.id}, anchor='{self.anchor_text}')>"


# Create indexes for better query performance
Index(
    "idx_encyclopedia_entries_status_published",
    EncyclopediaEntry.status,
    EncyclopediaEntry.published_at
)

Index(
    "idx_encyclopedia_conversations_entry_created",
    EncyclopediaConversation.entry_id,
    EncyclopediaConversation.created_at
)

Index(
    "idx_encyclopedia_links_source_target",
    EncyclopediaLink.source_entry_id,
    EncyclopediaLink.target_entry_id,
    unique=True
)