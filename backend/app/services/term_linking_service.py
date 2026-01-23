"""
Term Linking Service for Educational Content Integration.

This service provides automatic detection and linking of poker terms throughout
the application interface, with hover previews and modal displays for definitions.
"""

import logging
import re
from typing import List, Dict, Optional, Set, Tuple, Any
from uuid import UUID
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..models.encyclopedia import EncyclopediaEntry, EncyclopediaStatus
from ..models.education import EducationContent
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TermDefinition:
    """Definition data for a poker term."""
    term: str
    definition: str
    explanation: Optional[str] = None
    source_type: str = "encyclopedia"  # "encyclopedia" or "education"
    source_id: str = ""
    context_appropriate: bool = True
    difficulty_level: Optional[str] = None
    category: Optional[str] = None


@dataclass
class TermLink:
    """A detected term link in content."""
    term: str
    start_position: int
    end_position: int
    definition: TermDefinition
    confidence: float = 1.0


@dataclass
class LinkedContent:
    """Content with detected and linked terms."""
    original_content: str
    linked_content: str
    detected_terms: List[TermLink]
    link_count: int


class TermLinkingService:
    """Service for detecting and linking poker terms in content."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the term linking service."""
        self.db = db
        self._term_cache: Dict[str, TermDefinition] = {}
        self._term_patterns: Dict[str, re.Pattern] = {}
        self._cache_loaded = False
    
    async def load_term_cache(self) -> None:
        """Load all available terms into cache for fast lookup."""
        if self._cache_loaded:
            return
        
        try:
            # Load encyclopedia entries
            encyclopedia_result = await self.db.execute(
                select(EncyclopediaEntry)
                .where(EncyclopediaEntry.status == EncyclopediaStatus.PUBLISHED)
            )
            encyclopedia_entries = encyclopedia_result.scalars().all()
            
            # Load education content
            education_result = await self.db.execute(
                select(EducationContent)
                .where(EducationContent.is_published == True)
            )
            education_entries = education_result.scalars().all()
            
            # Build term cache from encyclopedia
            for entry in encyclopedia_entries:
                term_key = entry.title.lower().strip()
                self._term_cache[term_key] = TermDefinition(
                    term=entry.title,
                    definition=self._extract_first_sentence(entry.content),
                    explanation=entry.content,
                    source_type="encyclopedia",
                    source_id=entry.id,
                    context_appropriate=True
                )
                
                # Create regex pattern for term detection
                # Escape special regex characters and create word boundary pattern
                escaped_term = re.escape(entry.title)
                pattern = rf'\b{escaped_term}\b'
                self._term_patterns[term_key] = re.compile(pattern, re.IGNORECASE)
            
            # Build term cache from education content
            for content in education_entries:
                term_key = content.title.lower().strip()
                if term_key not in self._term_cache:  # Encyclopedia takes precedence
                    self._term_cache[term_key] = TermDefinition(
                        term=content.title,
                        definition=content.definition,
                        explanation=content.explanation,
                        source_type="education",
                        source_id=str(content.id),
                        context_appropriate=True,
                        difficulty_level=content.difficulty.value if content.difficulty else None,
                        category=content.category.value if content.category else None
                    )
                    
                    # Create regex pattern
                    escaped_term = re.escape(content.title)
                    pattern = rf'\b{escaped_term}\b'
                    self._term_patterns[term_key] = re.compile(pattern, re.IGNORECASE)
            
            self._cache_loaded = True
            logger.info(f"Loaded {len(self._term_cache)} terms into linking cache")
            
        except Exception as e:
            logger.error(f"Failed to load term cache: {e}")
            # Continue with empty cache - graceful degradation
    
    async def detect_terms_in_content(
        self,
        content: str,
        context: Optional[str] = None,
        max_links: int = 10
    ) -> LinkedContent:
        """
        Detect poker terms in content and return linked version.
        
        Args:
            content: The text content to analyze
            context: Optional context for term selection (e.g., "analysis", "dashboard")
            max_links: Maximum number of terms to link
            
        Returns:
            LinkedContent with detected terms and linked version
        """
        await self.load_term_cache()
        
        if not content or not self._term_cache:
            return LinkedContent(
                original_content=content,
                linked_content=content,
                detected_terms=[],
                link_count=0
            )
        
        detected_terms: List[TermLink] = []
        used_positions: Set[Tuple[int, int]] = set()
        
        # Detect terms using regex patterns
        for term_key, pattern in self._term_patterns.items():
            if len(detected_terms) >= max_links:
                break
                
            term_def = self._term_cache[term_key]
            
            # Skip if not context-appropriate
            if not self._is_context_appropriate(term_def, context):
                continue
            
            # Find all matches
            for match in pattern.finditer(content):
                start, end = match.span()
                
                # Check for overlapping positions
                if any(self._positions_overlap((start, end), used_pos) for used_pos in used_positions):
                    continue
                
                # Create term link
                term_link = TermLink(
                    term=match.group(),
                    start_position=start,
                    end_position=end,
                    definition=term_def,
                    confidence=self._calculate_confidence(match.group(), term_def, context)
                )
                
                detected_terms.append(term_link)
                used_positions.add((start, end))
                
                if len(detected_terms) >= max_links:
                    break
        
        # Sort by position for consistent linking
        detected_terms.sort(key=lambda x: x.start_position)
        
        # Generate linked content
        linked_content = self._generate_linked_content(content, detected_terms)
        
        return LinkedContent(
            original_content=content,
            linked_content=linked_content,
            detected_terms=detected_terms,
            link_count=len(detected_terms)
        )
    
    async def get_term_definition(
        self,
        term: str,
        context: Optional[str] = None
    ) -> Optional[TermDefinition]:
        """
        Get definition for a specific term.
        
        Args:
            term: The term to look up
            context: Optional context for definition selection
            
        Returns:
            TermDefinition if found, None otherwise
        """
        await self.load_term_cache()
        
        term_key = term.lower().strip()
        definition = self._term_cache.get(term_key)
        
        if definition and self._is_context_appropriate(definition, context):
            return definition
        
        return None
    
    async def get_related_terms(
        self,
        term: str,
        limit: int = 5
    ) -> List[TermDefinition]:
        """
        Get terms related to the given term.
        
        Args:
            term: The base term
            limit: Maximum number of related terms
            
        Returns:
            List of related term definitions
        """
        await self.load_term_cache()
        
        term_key = term.lower().strip()
        base_definition = self._term_cache.get(term_key)
        
        if not base_definition:
            return []
        
        related_terms = []
        
        # Find terms with similar categories or difficulty levels
        for other_term_key, other_def in self._term_cache.items():
            if other_term_key == term_key:
                continue
            
            if len(related_terms) >= limit:
                break
            
            # Check for category match
            if (base_definition.category and other_def.category and 
                base_definition.category == other_def.category):
                related_terms.append(other_def)
                continue
            
            # Check for difficulty level match
            if (base_definition.difficulty_level and other_def.difficulty_level and
                base_definition.difficulty_level == other_def.difficulty_level):
                related_terms.append(other_def)
                continue
            
            # Check for content similarity (simple keyword matching)
            if self._has_content_similarity(base_definition, other_def):
                related_terms.append(other_def)
        
        return related_terms[:limit]
    
    async def get_term_suggestions(
        self,
        partial_term: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get term suggestions based on partial input.
        
        Args:
            partial_term: Partial term to match
            limit: Maximum number of suggestions
            
        Returns:
            List of matching term names
        """
        await self.load_term_cache()
        
        if not partial_term or len(partial_term) < 2:
            return []
        
        partial_lower = partial_term.lower()
        suggestions = []
        
        for term_key, term_def in self._term_cache.items():
            if len(suggestions) >= limit:
                break
                
            if partial_lower in term_key:
                suggestions.append(term_def.term)
        
        return sorted(suggestions)[:limit]
    
    async def refresh_cache(self) -> None:
        """Refresh the term cache with latest data."""
        self._term_cache.clear()
        self._term_patterns.clear()
        self._cache_loaded = False
        await self.load_term_cache()
    
    def _extract_first_sentence(self, content: str) -> str:
        """Extract the first sentence from content for definition."""
        if not content:
            return ""
        
        # Simple sentence extraction - look for first period, exclamation, or question mark
        sentences = re.split(r'[.!?]+', content.strip())
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 200:
                # Truncate if too long
                return first_sentence[:197] + "..."
            return first_sentence
        
        return content[:200] + "..." if len(content) > 200 else content
    
    def _is_context_appropriate(
        self,
        term_def: TermDefinition,
        context: Optional[str]
    ) -> bool:
        """Check if a term definition is appropriate for the given context."""
        if not context:
            return True
        
        # Context-specific filtering logic
        context_lower = context.lower()
        
        # For analysis context, prefer advanced terms
        if context_lower in ["analysis", "statistics", "advanced"]:
            if term_def.difficulty_level == "beginner":
                return False
        
        # For dashboard context, prefer basic terms
        if context_lower in ["dashboard", "overview", "basic"]:
            if term_def.difficulty_level == "advanced":
                return False
        
        return True
    
    def _calculate_confidence(
        self,
        matched_text: str,
        term_def: TermDefinition,
        context: Optional[str]
    ) -> float:
        """Calculate confidence score for a term match."""
        confidence = 1.0
        
        # Exact case match increases confidence
        if matched_text == term_def.term:
            confidence += 0.1
        
        # Context appropriateness affects confidence
        if context and self._is_context_appropriate(term_def, context):
            confidence += 0.1
        
        # Source type affects confidence (encyclopedia preferred)
        if term_def.source_type == "encyclopedia":
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _positions_overlap(
        self,
        pos1: Tuple[int, int],
        pos2: Tuple[int, int]
    ) -> bool:
        """Check if two position ranges overlap."""
        start1, end1 = pos1
        start2, end2 = pos2
        return not (end1 <= start2 or end2 <= start1)
    
    def _generate_linked_content(
        self,
        content: str,
        detected_terms: List[TermLink]
    ) -> str:
        """Generate HTML content with term links."""
        if not detected_terms:
            return content
        
        # Sort by position in reverse order to maintain positions during replacement
        sorted_terms = sorted(detected_terms, key=lambda x: x.start_position, reverse=True)
        
        linked_content = content
        
        for term_link in sorted_terms:
            start = term_link.start_position
            end = term_link.end_position
            term_text = term_link.term
            
            # Create link HTML with data attributes for frontend handling
            link_html = (
                f'<span class="poker-term-link" '
                f'data-term="{term_text}" '
                f'data-source-type="{term_link.definition.source_type}" '
                f'data-source-id="{term_link.definition.source_id}" '
                f'data-definition="{self._escape_html_attr(term_link.definition.definition)}" '
                f'title="{self._escape_html_attr(term_link.definition.definition)}">'
                f'{term_text}'
                f'</span>'
            )
            
            # Replace the term with the link
            linked_content = linked_content[:start] + link_html + linked_content[end:]
        
        return linked_content
    
    def _escape_html_attr(self, text: str) -> str:
        """Escape text for use in HTML attributes."""
        if not text:
            return ""
        
        return (text.replace('&', '&amp;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))
    
    def _has_content_similarity(
        self,
        def1: TermDefinition,
        def2: TermDefinition
    ) -> bool:
        """Check if two definitions have content similarity."""
        # Simple keyword-based similarity check
        keywords1 = set(def1.definition.lower().split())
        keywords2 = set(def2.definition.lower().split())
        
        # Remove common words
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were"}
        keywords1 -= common_words
        keywords2 -= common_words
        
        if not keywords1 or not keywords2:
            return False
        
        # Calculate Jaccard similarity
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return (intersection / union) > 0.2 if union > 0 else False