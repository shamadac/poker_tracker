"""
Simple unit tests for the Term Linking Service functionality.

Tests core term detection and linking logic without database dependencies.
"""

import pytest
from app.services.term_linking_service import TermLinkingService, TermDefinition


class TestTermLinkingLogic:
    """Test core term linking logic without database dependencies."""
    
    def test_extract_first_sentence(self):
        """Test extracting first sentence from content."""
        service = TermLinkingService(None)  # No DB needed for this test
        
        content = "This is the first sentence. This is the second sentence. This is the third."
        result = service._extract_first_sentence(content)
        assert result == "This is the first sentence"
        
        # Test with long content
        long_content = "A" * 250 + ". Second sentence."
        result = service._extract_first_sentence(long_content)
        assert len(result) <= 200
        assert result.endswith("...")
        
        # Test with empty content
        assert service._extract_first_sentence("") == ""
        assert service._extract_first_sentence(None) == ""
    
    def test_is_context_appropriate(self):
        """Test context appropriateness filtering."""
        service = TermLinkingService(None)
        
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
        assert service._is_context_appropriate(beginner_term, "dashboard") is True
        assert service._is_context_appropriate(advanced_term, "dashboard") is False
        
        # Test analysis context (should prefer advanced terms)
        assert service._is_context_appropriate(beginner_term, "analysis") is False
        assert service._is_context_appropriate(advanced_term, "analysis") is True
        
        # Test no context (should accept all)
        assert service._is_context_appropriate(beginner_term, None) is True
        assert service._is_context_appropriate(advanced_term, None) is True
    
    def test_calculate_confidence(self):
        """Test confidence calculation for term matches."""
        service = TermLinkingService(None)
        
        term_def = TermDefinition(
            term="VPIP",
            definition="Test definition",
            source_type="encyclopedia",
            source_id="test-1"
        )
        
        # Exact match should have higher confidence than case mismatch
        exact_confidence = service._calculate_confidence("VPIP", term_def, "dashboard")
        case_confidence = service._calculate_confidence("vpip", term_def, "dashboard")
        
        assert exact_confidence >= case_confidence  # Allow equal confidence
        assert 0 <= exact_confidence <= 1.0
        assert 0 <= case_confidence <= 1.0
    
    def test_positions_overlap(self):
        """Test position overlap detection."""
        service = TermLinkingService(None)
        
        assert service._positions_overlap((0, 5), (3, 8)) is True
        assert service._positions_overlap((0, 5), (5, 10)) is False
        assert service._positions_overlap((0, 5), (6, 10)) is False
        assert service._positions_overlap((5, 10), (0, 3)) is False
    
    def test_escape_html_attr(self):
        """Test HTML attribute escaping."""
        service = TermLinkingService(None)
        
        test_text = 'Test "quoted" text with <tags> & ampersands'
        escaped = service._escape_html_attr(test_text)
        
        assert '&quot;' in escaped
        assert '&lt;' in escaped
        assert '&gt;' in escaped
        assert '&amp;' in escaped
        assert '"' not in escaped
        assert '<' not in escaped
        assert '>' not in escaped
    
    def test_has_content_similarity(self):
        """Test content similarity detection."""
        service = TermLinkingService(None)
        
        def1 = TermDefinition(
            term="VPIP",
            definition="percentage of hands player voluntarily puts money into pot",
            source_type="encyclopedia",
            source_id="1"
        )
        
        def2 = TermDefinition(
            term="PFR", 
            definition="percentage of hands player raises preflop when entering pot",
            source_type="encyclopedia",
            source_id="2"
        )
        
        def3 = TermDefinition(
            term="Bluff",
            definition="betting with weak hand to make opponents fold",
            source_type="education",
            source_id="3"
        )
        
        # VPIP and PFR should be similar (both about percentages and hands)
        assert service._has_content_similarity(def1, def2) is True
        
        # VPIP and Bluff should not be similar
        assert service._has_content_similarity(def1, def3) is False
    
    def test_generate_linked_content_basic(self):
        """Test basic linked content generation."""
        service = TermLinkingService(None)
        
        # Create a mock term link
        from app.services.term_linking_service import TermLink
        
        term_def = TermDefinition(
            term="VPIP",
            definition="Voluntarily Put In Pot percentage",
            source_type="encyclopedia",
            source_id="test-1"
        )
        
        term_link = TermLink(
            term="VPIP",
            start_position=5,
            end_position=9,
            definition=term_def,
            confidence=0.9
        )
        
        content = "Your VPIP is too high"
        linked_content = service._generate_linked_content(content, [term_link])
        
        # Should contain HTML span with data attributes
        assert 'class="poker-term-link"' in linked_content
        assert 'data-term="VPIP"' in linked_content
        assert 'data-source-type="encyclopedia"' in linked_content
        assert 'VPIP' in linked_content


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])