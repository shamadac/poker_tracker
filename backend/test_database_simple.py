"""
Simple test to verify database schema property test works.
"""
import pytest
from hypothesis import given, strategies as st

def test_simple():
    """Simple test that should be discovered."""
    assert True

@given(st.integers())
def test_hypothesis_works(x):
    """Test that hypothesis works."""
    assert isinstance(x, int)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])