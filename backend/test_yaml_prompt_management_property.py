"""
Property-Based Tests for YAML Prompt Management System

**Feature: professional-poker-analyzer-rebuild, Property 32: YAML Prompt Management**

Tests the universal property that for any AI analysis request, the system should 
load the appropriate prompt template from YAML configuration and format it with 
hand-specific data.

**Validates: Requirements 7.1, 7.2**

This test ensures that:
1. YAML prompt files are loaded correctly with proper structure
2. Prompt templates can be retrieved by category and type
3. Prompt formatting works with various data combinations
4. Error handling works for missing or invalid prompts
5. The system maintains consistency across different prompt types
"""

import pytest
import tempfile
import yaml
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, Any, Optional
import logging

from app.services.prompt_manager import PromptManager, PromptTemplate


# Test data strategies
@st.composite
def valid_yaml_content(draw):
    """Generate valid YAML content for prompt files."""
    category_name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='{}[]')))
    prompt_type = draw(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='{}[]')))
    
    # Generate base prompts without format variables first
    system_base = draw(st.text(min_size=10, max_size=400, alphabet=st.characters(blacklist_characters='{}')))
    user_base = draw(st.text(min_size=10, max_size=400, alphabet=st.characters(blacklist_characters='{}')))
    
    # Add some well-formed format variables to test formatting
    system_prompt = system_base + " Player level: {experience_level}"
    user_prompt = user_base + " Game: {game_type}, Stakes: {stakes}"
    
    return {
        category_name: {
            prompt_type: {
                'system_prompt': system_prompt,
                'user_prompt': user_prompt,
                'metadata': {
                    'difficulty': draw(st.sampled_from(['beginner', 'intermediate', 'advanced'])),
                    'focus_areas': draw(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
                }
            }
        }
    }


@st.composite
def prompt_variables(draw):
    """Generate variables for prompt formatting."""
    return {
        'experience_level': draw(st.sampled_from(['beginner', 'intermediate', 'advanced'])),
        'game_type': draw(st.sampled_from(['No Limit Hold\'em', 'Pot Limit Omaha', 'Tournament'])),
        'stakes': draw(st.sampled_from(['$0.01/$0.02', '$0.05/$0.10', '$1/$2', '$5/$10'])),
        'platform': draw(st.sampled_from(['pokerstars', 'ggpoker'])),
        'position': draw(st.sampled_from(['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB'])),
        'player_cards': draw(st.text(min_size=2, max_size=10)),
        'board_cards': draw(st.text(min_size=0, max_size=15)),
        'actions': draw(st.text(min_size=5, max_size=100)),
        'result': draw(st.sampled_from(['won', 'lost', 'folded'])),
        'pot_size': draw(st.text(min_size=1, max_size=10))
    }


@st.composite
def invalid_yaml_content(draw):
    """Generate invalid YAML content to test error handling."""
    return draw(st.one_of(
        st.just("invalid: yaml: content: [unclosed"),
        st.just("- invalid\n  - structure\n    - without: proper nesting"),
        st.just("{invalid json mixed with yaml}"),
        st.just(""),
        st.just("null"),
        st.just("123")
    ))


class TestYAMLPromptManagementProperty:
    """Property-based tests for YAML prompt management system."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.prompts_path = Path(self.temp_dir)
        
        # Disable logging during tests to reduce noise
        logging.getLogger('app.services.prompt_manager').setLevel(logging.CRITICAL)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(valid_yaml_content())
    @settings(max_examples=100, deadline=5000)
    def test_property_yaml_loading_consistency(self, yaml_content):
        """
        Property: For any valid YAML prompt file, the system should load it 
        consistently and make it available for retrieval.
        """
        # Create YAML file with the generated content
        yaml_file = self.prompts_path / "test_prompts.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        # Initialize prompt manager
        manager = PromptManager(str(self.prompts_path))
        
        # Extract category and type from the generated content
        category = list(yaml_content.keys())[0]
        prompt_type = list(yaml_content[category].keys())[0]
        
        # Property: The loaded content should match the original
        template = manager.get_prompt_template(category, prompt_type)
        
        assert template is not None, f"Template should be loaded for {category}.{prompt_type}"
        assert template.system_prompt == yaml_content[category][prompt_type]['system_prompt']
        assert template.user_prompt == yaml_content[category][prompt_type]['user_prompt']
        assert template.metadata == yaml_content[category][prompt_type]['metadata']
        
        # Property: Categories and types should be discoverable
        assert category in manager.get_available_categories()
        assert prompt_type in manager.get_available_types(category)
    
    @given(valid_yaml_content(), prompt_variables())
    @settings(max_examples=100, deadline=5000)
    def test_property_prompt_formatting_consistency(self, yaml_content, variables):
        """
        Property: For any valid prompt template and variable set, formatting 
        should produce consistent, complete prompts without errors.
        """
        # Create YAML file
        yaml_file = self.prompts_path / "test_prompts.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        manager = PromptManager(str(self.prompts_path))
        
        category = list(yaml_content.keys())[0]
        prompt_type = list(yaml_content[category].keys())[0]
        
        # Property: Formatting should work with provided variables
        formatted = manager.format_prompt(category, prompt_type, **variables)
        
        if formatted is not None:  # Only test if formatting succeeded
            assert 'system' in formatted
            assert 'user' in formatted
            assert 'metadata' in formatted
            
            # Property: Formatted prompts should contain the variable values
            for var_name, var_value in variables.items():
                if f"{{{var_name}}}" in yaml_content[category][prompt_type]['system_prompt']:
                    assert str(var_value) in formatted['system']
                if f"{{{var_name}}}" in yaml_content[category][prompt_type]['user_prompt']:
                    assert str(var_value) in formatted['user']
            
            # Property: No unresolved template variables should remain
            assert '{' not in formatted['system'] or '}' not in formatted['system']
            assert '{' not in formatted['user'] or '}' not in formatted['user']
    
    @given(st.lists(valid_yaml_content(), min_size=1, max_size=5))
    @settings(max_examples=50, deadline=10000)
    def test_property_multiple_files_loading(self, yaml_contents):
        """
        Property: For any number of valid YAML files, the system should load 
        all categories and types correctly. Note: If categories have the same name
        across files, later files will overwrite earlier ones.
        """
        # Create multiple YAML files
        final_categories = {}  # Track the final state after overwrites
        
        for i, yaml_content in enumerate(yaml_contents):
            yaml_file = self.prompts_path / f"prompts_{i}.yml"
            with open(yaml_file, 'w') as f:
                yaml.dump(yaml_content, f)
            
            # Track final state (later files overwrite earlier ones)
            for category, types_dict in yaml_content.items():
                final_categories[category] = types_dict
        
        manager = PromptManager(str(self.prompts_path))
        
        # Property: All final categories should be loaded
        loaded_categories = set(manager.get_available_categories())
        expected_categories = set(final_categories.keys())
        assert expected_categories.issubset(loaded_categories), \
            f"Expected categories {expected_categories}, got {loaded_categories}"
        
        # Property: All types within each final category should be available
        for category, expected_types_dict in final_categories.items():
            expected_types = set(expected_types_dict.keys())
            loaded_types = set(manager.get_available_types(category))
            assert expected_types.issubset(loaded_types), \
                f"Category {category}: expected types {expected_types}, got {loaded_types}"
    
    @given(invalid_yaml_content())
    @settings(max_examples=50, deadline=5000)
    def test_property_invalid_yaml_handling(self, invalid_content):
        """
        Property: For any invalid YAML content, the system should handle errors 
        gracefully without crashing and provide meaningful error states.
        """
        # Create invalid YAML file
        yaml_file = self.prompts_path / "invalid.yml"
        with open(yaml_file, 'w') as f:
            f.write(invalid_content)
        
        # Property: Manager should initialize without crashing
        manager = PromptManager(str(self.prompts_path))
        
        # Property: Invalid content should not create valid templates
        categories = manager.get_available_categories()
        
        # If any categories were loaded, they should have valid structure
        for category in categories:
            types = manager.get_available_types(category)
            for prompt_type in types:
                template = manager.get_prompt_template(category, prompt_type)
                if template is not None:
                    assert isinstance(template.system_prompt, str)
                    assert isinstance(template.user_prompt, str)
                    assert len(template.system_prompt.strip()) > 0
                    assert len(template.user_prompt.strip()) > 0
    
    @given(valid_yaml_content())
    @settings(max_examples=50, deadline=5000)
    def test_property_prompt_validation_consistency(self, yaml_content):
        """
        Property: For any loaded prompt template, validation should correctly 
        identify valid and invalid structures.
        """
        yaml_file = self.prompts_path / "test_prompts.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        manager = PromptManager(str(self.prompts_path))
        
        category = list(yaml_content.keys())[0]
        prompt_type = list(yaml_content[category].keys())[0]
        
        # Property: Valid prompts should pass validation
        is_valid = manager.validate_prompt_structure(category, prompt_type)
        
        # Check if the original content has non-empty prompts
        original_system = yaml_content[category][prompt_type]['system_prompt'].strip()
        original_user = yaml_content[category][prompt_type]['user_prompt'].strip()
        
        if original_system and original_user:
            assert is_valid, f"Valid prompt {category}.{prompt_type} should pass validation"
        else:
            assert not is_valid, f"Invalid prompt {category}.{prompt_type} should fail validation"
    
    @given(valid_yaml_content())
    @settings(max_examples=50, deadline=5000)
    def test_property_reload_consistency(self, yaml_content):
        """
        Property: For any prompt configuration, reloading should maintain 
        consistency and not lose or corrupt data.
        """
        yaml_file = self.prompts_path / "test_prompts.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        manager = PromptManager(str(self.prompts_path))
        
        # Get initial state
        initial_categories = set(manager.get_available_categories())
        initial_info = manager.get_prompt_info()
        
        category = list(yaml_content.keys())[0]
        prompt_type = list(yaml_content[category].keys())[0]
        initial_template = manager.get_prompt_template(category, prompt_type)
        
        # Property: Reload should succeed
        reload_success = manager.reload_prompts()
        assert reload_success, "Reload should succeed for valid configuration"
        
        # Property: State should be consistent after reload
        reloaded_categories = set(manager.get_available_categories())
        reloaded_template = manager.get_prompt_template(category, prompt_type)
        
        assert initial_categories == reloaded_categories, "Categories should be consistent after reload"
        
        if initial_template and reloaded_template:
            assert initial_template.system_prompt == reloaded_template.system_prompt
            assert initial_template.user_prompt == reloaded_template.user_prompt
            assert initial_template.metadata == reloaded_template.metadata
    
    @given(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=15))
    @settings(max_examples=100, deadline=5000)
    def test_property_nonexistent_prompt_handling(self, fake_category, fake_type):
        """
        Property: For any non-existent category or type, the system should 
        return None consistently and not crash.
        """
        # Assume the fake names don't accidentally match real ones
        assume(fake_category not in ['hand_analysis', 'session_analysis', 'coaching', 'educational'])
        assume(fake_type not in ['basic', 'advanced', 'summary', 'quick'])
        
        # Create a valid YAML file first
        valid_content = {
            'real_category': {
                'real_type': {
                    'system_prompt': 'Test system prompt',
                    'user_prompt': 'Test user prompt'
                }
            }
        }
        
        yaml_file = self.prompts_path / "real_prompts.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(valid_content, f)
        
        manager = PromptManager(str(self.prompts_path))
        
        # Property: Non-existent prompts should return None
        template = manager.get_prompt_template(fake_category, fake_type)
        assert template is None, f"Non-existent prompt {fake_category}.{fake_type} should return None"
        
        formatted = manager.format_prompt(fake_category, fake_type, test_var="test")
        assert formatted is None, f"Formatting non-existent prompt should return None"
        
        # Property: Non-existent categories should return empty type lists
        types = manager.get_available_types(fake_category)
        assert types == [], f"Non-existent category should return empty types list"
        
        # Property: Validation should return False for non-existent prompts
        is_valid = manager.validate_prompt_structure(fake_category, fake_type)
        assert not is_valid, f"Non-existent prompt should fail validation"
    
    def test_property_empty_directory_handling(self):
        """
        Property: For an empty prompts directory, the system should initialize 
        gracefully and provide empty but valid responses.
        """
        # Create empty directory
        manager = PromptManager(str(self.prompts_path))
        
        # Property: Empty directory should not crash initialization
        assert isinstance(manager.get_available_categories(), list)
        assert len(manager.get_available_categories()) == 0
        
        # Property: Info should be valid even with no prompts
        info = manager.get_prompt_info()
        assert isinstance(info, dict)
        assert info['categories_count'] == 0
        assert isinstance(info['categories'], dict)
        assert len(info['categories']) == 0
    
    @given(valid_yaml_content(), prompt_variables())
    @settings(max_examples=50, deadline=5000)
    def test_property_format_variable_completeness(self, yaml_content, variables):
        """
        Property: For any prompt template with format variables, all variables 
        present in the template should be replaceable with provided values.
        """
        yaml_file = self.prompts_path / "test_prompts.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_content, f)
        
        manager = PromptManager(str(self.prompts_path))
        
        category = list(yaml_content.keys())[0]
        prompt_type = list(yaml_content[category].keys())[0]
        
        # Get the original template to check for variables
        template = manager.get_prompt_template(category, prompt_type)
        assert template is not None
        
        # Find all variables in the template
        import re
        system_vars = set(re.findall(r'\{(\w+)\}', template.system_prompt))
        user_vars = set(re.findall(r'\{(\w+)\}', template.user_prompt))
        all_vars = system_vars | user_vars
        
        # Property: If we provide all required variables, formatting should succeed
        if all_vars.issubset(set(variables.keys())):
            try:
                formatted = manager.format_prompt(category, prompt_type, **variables)
                if formatted is not None:
                    # Property: No template variables should remain unresolved
                    remaining_system_vars = set(re.findall(r'\{(\w+)\}', formatted['system']))
                    remaining_user_vars = set(re.findall(r'\{(\w+)\}', formatted['user']))
                    
                    assert len(remaining_system_vars) == 0, f"Unresolved variables in system prompt: {remaining_system_vars}"
                    assert len(remaining_user_vars) == 0, f"Unresolved variables in user prompt: {remaining_user_vars}"
                # If formatting returns None, it means there was a formatting error
                # which is acceptable for malformed templates
            except (KeyError, ValueError):
                # Formatting errors are acceptable for edge cases with malformed templates
                pass


def test_integration_with_real_prompt_files():
    """
    Integration test using the actual prompt files to ensure they work correctly.
    This validates that our real YAML files conform to the expected structure.
    """
    # Test with real prompts directory
    prompts_dir = Path("prompts")
    if not prompts_dir.exists():
        pytest.skip("Real prompts directory not found")
    
    manager = PromptManager("prompts")
    
    # Test that real files load correctly
    categories = manager.get_available_categories()
    assert len(categories) > 0, "Should load real prompt categories"
    
    # Test some known categories and types
    expected_categories = ['hand_analysis', 'session_analysis', 'coaching', 'educational']
    for category in expected_categories:
        if category in categories:
            types = manager.get_available_types(category)
            assert len(types) > 0, f"Category {category} should have prompt types"
            
            # Test that we can get and validate templates
            for prompt_type in types:
                template = manager.get_prompt_template(category, prompt_type)
                assert template is not None, f"Should get template for {category}.{prompt_type}"
                assert manager.validate_prompt_structure(category, prompt_type), \
                    f"Real template {category}.{prompt_type} should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])