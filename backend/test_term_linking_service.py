"""
Unit tests for the Term Linking Service.

Tests the educational term linking functionality including term detection,
hover previews, and modal displays for poker terminology.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.term_linking_service import TermLinkingService, TermDefinition, TermLink, LinkedContent
from app.models.encyclopedia import EncyclopediaEntry, EncyclopediaStatus
from app.models.education import EducationContent, DifficultyLevel, ContentCategory


class TestTermLinkingService:
    """Test cases for the TermLinkingService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def term_service(self, mock_db):
        """Create a TermLinkingService instance with mocked database."""
        return TermLinkingService(mock_db)
    
    @pytest.fixture
    def sample_encyclopedia_entries(self):
        """Create sample encyclopedia entries for testing."""
        return [
            EncyclopediaEntry(
                id="enc-1",
                title="VPIP",
                content="VPIP (Voluntarily Put In Pot) is the percentage of hands a player voluntarily puts money into the pot preflop. This is one of the most fundamental poker statistics used to measure how tight or loose a player is.",
                status=EncyclopediaStatus.PUBLISHED
            ),
            EncyclopediaEntry(
                id="enc-2", 
                title="PFR",
                content="PFR (Preflop Raise) is the percentage of hands a player raises preflop when they enter the pot. The gap between VPIP and PFR shows how often a player limps versus raises.",
                status=EncyclopediaStatus.PUBLISHED
            ),
            EncyclopediaEntry(
                id="enc-3",
                title="C-Bet",
                content="A continuation bet (c-bet) is a bet made by the preflop aggressor on the flop, continuing their aggressive line from preflop.",
                status=EncyclopediaStatus.PUBLISHED
            )
        ]
    
    @pytest.fixture
    def sample_education_content(self):
        """Create sample education content for testing."""
        return [
            EducationContent(
                id="edu-1",
                title="Position",
                slug="position",
                category=ContentCategory.BASIC,
                difficulty=DifficultyLevel.BEGINNER,
                definition="Position refers to where a player sits relative to the dealer button and the order in which they act.",
                explanation="Position is one of the most important concepts in poker. Players in late position have more information and can make better decisions.",
                is_published=True
            ),
            EducationContent(
                id="edu-2",
                title="Bluff",
                slug="bluff",
                category=ContentCategory.ADVANCED,
                difficulty=DifficultyLevel.INTERMEDIATE,
                definition="A bluff is a bet or raise made with a weak hand to try to get opponents to fold better hands.",
                explanation="Bluffing is an essential part of poker strategy that allows players to win pots without having the best hand.",
                is_published=True
            )
        ]
    
    @pytest.mark.asyncio
    async def test_load_term_cache(self, term_service, mock_db, sample_encyclopedia_entries, sample_education_content):
        """Test loading terms into cache from encyclopedia and education content."""
        # Mock database queries
        mock_db.execute.side_effect = [
            # Encyclopedia entries query
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_encyclopedia_entries)))),
            # Education content query  
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_education_content))))
        ]
        
        await term_service.load_term_cache()
        
        # Verify cache is populated
        assert term_service._cache_loaded is True
        assert len(term_service._term_cache) == 5  # 3 encyclopedia + 2 education
        
        # Check specific terms
        assert "vpip" in term_service._term_cache
        assert "position" in term_service._term_cache
        
        # Verify term definitions
        vpip_def = term_service._term_cache["vpip"]
        assert vpip_def.term == "VPIP"
        assert vpip_def.source_type == "encyclopedia"
        assert "percentage of hands" in vpip_def.definition
        
        position_def = term_service._term_cache["position"]
        assert position_def.term == "Position"
        assert position_def.source_type == "education"
        assert position_def.difficulty_level == "beginner"
    
    @pytest.mark.asyncio
    async def test_detect_terms_in_content(self, term_service, mock_db, sample_encyclopedia_entries, sample_education_content):
        """Test detecting poker terms in content."""
        # Setup cache
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_encyclopedia_entries)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_education_content))))
        ]
        
        test_content = "Your VPIP is too high and your PFR needs work. Position is important for making good decisions."
        
        result = await term_service.detect_terms_in_content(test_content, context="analysis", max_links=5)
        
        assert isinstance(result, LinkedContent)
        assert result.original_content == test_content
        assert result.link_count > 0
        assert len(result.detected_terms) > 0
        
        # Check that terms were detected
        detected_term_names = [term.term for term in result.detected_terms]
        assert "VPIP" in detected_term_names
        assert "PFR" in detected_term_names
        assert "Position" in detected_term_names
        
        # Verify linked content contains HTML spans
        assert 'class="poker-term-link"' in result.linked_content
        assert 'data-term="VPIP"' in result.linked_content
    
    @pytest.mark.asyncio
    async def test_get_term_definition(self, term_service, mock_db, sample_encyclopedia_entries):
        """Test retrieving definition for a specific term."""
        # Setup cache
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_encyclopedia_entries)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        ]
        
        definition = await term_service.get_term_definition("VPIP", context="dashboard")
        
        assert definition is not None
        assert isinstance(definition, TermDefinition)
        assert definition.term == "VPIP"
        assert definition.source_type == "encyclopedia"
        assert "percentage of hands" in definition.definition
        
        # Test non-existent term
        no_definition = await term_service.get_term_definition("NonExistentTerm")
        assert no_definition is None
    
    @pytest.mark.asyncio
    async def test_get_related_terms(self, term_service, mock_db, sample_encyclopedia_entries, sample_education_content):
        """Test getting related terms for a given term."""
        # Setup cache
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_encyclopedia_entries)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_education_content))))
        ]
        
        related_terms = await term_service.get_related_terms("VPIP", limit=3)
        
        assert isinstance(related_terms, list)
        assert len(related_terms) <= 3
        
        # Should not include the original term
        related_term_names = [term.term for term in related_terms]
        assert "VPIP" not in related_term_names
    
    @pytest.mark.asyncio
    async def test_get_term_suggestions(self, term_service, mock_db, sample_encyclopedia_entries):
        """Test getting term suggestions based on partial input."""
        # Setup cache
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_encyclopedia_entries)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        ]
        
        suggestions = await term_service.get_term_suggestions("vp", limit=5)
        
        assert isinstance(suggestions, list)
        assert "VPIP" in suggestions
        
        # Test with too short input
        no_suggestions = await term_service.get_term_suggestions("v", limit=5)
        assert len(no_suggestions) == 0
    
    def test_extract_first_sentence(self, term_service):
        """Test extracting first sentence from content."""
        content = "This is the first sentence. This is the second sentence. This is the third."
        result = term_service._extract_first_sentence(content)
        assert result == "This is the first sentence"
        
        # Test with long content
        long_content = "A" * 250 + ". Second sentence."
        result = term_service._extract_first_sentence(long_content)
        assert len(result) <= 200
        assert result.endswith("...")
    
    def test_is_context_appropriate(self, term_service):
        """Test context appropriateness filtering."""
        beginner_term = TermDefinition(
            term="Test",
            definition="Test definition",
            source_type="education",
            source_id="test-1",
            difficulty_level="beginner"
        )
        
        advanced_term = TermDefinition(
            term="Advanced Test",
            definition="Advanced definition", 
            source_type="education",
            source_id="test-2",
            difficulty_level="advanced"
        )
        
        # Test dashboard context (should prefer basic terms)
        assert term_service._is_context_appropriate(beginner_term, "dashboard") is True
        assert term_service._is_context_appropriate(advanced_term, "dashboard") is False
        
        # Test analysis context (should prefer advanced terms)
        assert term_service._is_context_appropriate(beginner_term, "analysis") is False
        assert term_service._is_context_appropriate(advanced_term, "analysis") is True
        
        # Test no context (should accept all)
        assert term_service._is_context_appropriate(beginner_term, None) is True
        assert term_service._is_context_appropriate(advanced_term, None) is True
    
    def test_calculate_confidence(self, term_service):
        """Test confidence calculation for term matches."""
        term_def = TermDefinition(
            term="VPIP",
            definition="Test definition",
            source_type="encyclopedia",
            source_id="test-1"
        )
        
        # Exact match should have higher confidence
        exact_confidence = term_service._calculate_confidence("VPIP", term_def, "dashboard")
        case_confidence = term_service._calculate_confidence("vpip", term_def, "dashboard")
        
        assert exact_confidence > case_confidence
        assert 0 <= exact_confidence <= 1.0
        assert 0 <= case_confidence <= 1.0
    
    def test_positions_overlap(self, term_service):
        """Test position overlap detection."""
        assert term_service._positions_overlap((0, 5), (3, 8)) is True
        assert term_service._positions_overlap((0, 5), (5, 10)) is False
        assert term_service._positions_overlap((0, 5), (6, 10)) is False
        assert term_service._positions_overlap((5, 10), (0, 3)) is False
    
    def test_escape_html_attr(self, term_service):
        """Test HTML attribute escaping."""
        test_text = 'Test "quoted" text with <tags> & ampersands'
        escaped = term_service._escape_html_attr(test_text)
        
        assert '&quot;' in escaped
        assert '&lt;' in escaped
        assert '&gt;' in escaped
        assert '&amp;' in escaped
        assert '"' not in escaped
        assert '<' not in escaped
        assert '>' not in escaped
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, term_service):
        """Test handling of empty or None content."""
        result = await term_service.detect_terms_in_content("", context="test")
        assert result.original_content == ""
        assert result.linked_content == ""
        assert result.link_count == 0
        
        result = await term_service.detect_terms_in_content(None, context="test")
        assert result.original_content is None
        assert result.linked_content is None
        assert result.link_count == 0
    
    @pytest.mark.asyncio
    async def test_max_links_limit(self, term_service, mock_db, sample_encyclopedia_entries):
        """Test that max_links parameter is respected."""
        # Setup cache
        mock_db.execute.side_effect = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=sample_encyclopedia_entries)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))
        ]
        
        # Content with multiple terms
        content = "VPIP and PFR are important. C-Bet frequency matters too. VPIP again and PFR again."
        
        result = await term_service.detect_terms_in_content(content, max_links=2)
        
        assert result.link_count <= 2
        assert len(result.detected_terms) <= 2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])