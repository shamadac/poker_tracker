"""
YAML Prompt Management System

This service manages AI prompts stored in YAML configuration files,
providing template loading, formatting, and dynamic prompt generation
for poker hand and session analysis.

Requirements: 7.1, 7.2
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Represents a prompt template with system and user components."""
    system_prompt: str
    user_prompt: str
    metadata: Optional[Dict[str, Any]] = None


class PromptManager:
    """
    Manages YAML-based prompt templates for AI analysis.
    
    Provides functionality to:
    - Load prompt templates from YAML files
    - Format prompts with dynamic data
    - Manage different prompt categories and types
    - Support hot-reloading for development
    """
    
    def __init__(self, prompts_directory: str = "prompts"):
        """
        Initialize the prompt manager.
        
        Args:
            prompts_directory: Directory containing YAML prompt files
        """
        self.prompts_directory = Path(prompts_directory)
        self.prompts: Dict[str, Any] = {}
        self.last_loaded: Optional[datetime] = None
        
        # Ensure prompts directory exists
        self.prompts_directory.mkdir(exist_ok=True)
        
        # Load initial prompts
        self._load_all_prompts()
    
    def _load_all_prompts(self) -> None:
        """Load all YAML prompt files from the prompts directory."""
        try:
            self.prompts = {}
            
            if not self.prompts_directory.exists():
                logger.warning(f"Prompts directory {self.prompts_directory} does not exist")
                return
            
            yaml_files = list(self.prompts_directory.glob("*.yml")) + list(self.prompts_directory.glob("*.yaml"))
            
            if not yaml_files:
                logger.warning(f"No YAML files found in {self.prompts_directory}")
                return
            
            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        file_content = yaml.safe_load(f)
                        if file_content:
                            # Merge the content from this file into the main prompts dict
                            # The YAML files contain category names as top-level keys
                            for category, category_data in file_content.items():
                                if isinstance(category_data, dict):
                                    self.prompts[category] = category_data
                                    logger.info(f"Loaded category '{category}' from {yaml_file.name}")
                                else:
                                    logger.warning(f"Invalid structure in {yaml_file.name}: {category} is not a dict")
                        else:
                            logger.warning(f"Empty or invalid YAML file: {yaml_file.name}")
                            
                except yaml.YAMLError as e:
                    logger.error(f"Error parsing YAML file {yaml_file.name}: {e}")
                except Exception as e:
                    logger.error(f"Error loading prompt file {yaml_file.name}: {e}")
            
            self.last_loaded = datetime.now()
            logger.info(f"Loaded {len(self.prompts)} prompt categories")
            
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            self.prompts = {}
    
    def get_prompt_template(self, category: str, prompt_type: str) -> Optional[PromptTemplate]:
        """
        Get a prompt template by category and type.
        
        Args:
            category: Prompt category (e.g., 'hand_analysis', 'session_analysis')
            prompt_type: Prompt type within category (e.g., 'basic', 'advanced')
            
        Returns:
            PromptTemplate object or None if not found
        """
        try:
            if category not in self.prompts:
                logger.error(f"Prompt category '{category}' not found")
                return None
            
            category_prompts = self.prompts[category]
            if prompt_type not in category_prompts:
                logger.error(f"Prompt type '{prompt_type}' not found in category '{category}'")
                return None
            
            prompt_data = category_prompts[prompt_type]
            
            # Extract system and user prompts
            system_prompt = prompt_data.get('system_prompt', '')
            user_prompt = prompt_data.get('user_prompt', '')
            metadata = prompt_data.get('metadata', {})
            
            if not system_prompt or not user_prompt:
                logger.error(f"Missing system_prompt or user_prompt in {category}.{prompt_type}")
                return None
            
            return PromptTemplate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error getting prompt template {category}.{prompt_type}: {e}")
            return None
    
    def format_prompt(self, category: str, prompt_type: str, **kwargs) -> Optional[Dict[str, str]]:
        """
        Get formatted prompt with variables substituted.
        
        Args:
            category: Prompt category
            prompt_type: Prompt type within category
            **kwargs: Variables to substitute in the prompt template
            
        Returns:
            Dictionary with 'system' and 'user' formatted prompts, or None if error
        """
        try:
            template = self.get_prompt_template(category, prompt_type)
            if not template:
                return None
            
            # Format both system and user prompts
            formatted_system = template.system_prompt.format(**kwargs)
            formatted_user = template.user_prompt.format(**kwargs)
            
            return {
                'system': formatted_system,
                'user': formatted_user,
                'metadata': template.metadata or {}
            }
            
        except KeyError as e:
            logger.error(f"Missing required variable for prompt formatting: {e}")
            return None
        except Exception as e:
            logger.error(f"Error formatting prompt {category}.{prompt_type}: {e}")
            return None
    
    def get_available_categories(self) -> list[str]:
        """Get list of available prompt categories."""
        return list(self.prompts.keys())
    
    def get_available_types(self, category: str) -> list[str]:
        """Get list of available prompt types for a category."""
        if category not in self.prompts:
            return []
        return list(self.prompts[category].keys())
    
    def reload_prompts(self) -> bool:
        """
        Reload prompts from YAML files.
        
        Useful for development and dynamic prompt updates.
        
        Returns:
            True if reload was successful, False otherwise
        """
        try:
            old_count = len(self.prompts)
            self._load_all_prompts()
            new_count = len(self.prompts)
            
            logger.info(f"Reloaded prompts: {old_count} -> {new_count} categories")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload prompts: {e}")
            return False
    
    def validate_prompt_structure(self, category: str, prompt_type: str) -> bool:
        """
        Validate that a prompt has the required structure.
        
        Args:
            category: Prompt category
            prompt_type: Prompt type
            
        Returns:
            True if prompt structure is valid, False otherwise
        """
        try:
            template = self.get_prompt_template(category, prompt_type)
            if not template:
                return False
            
            # Check that both system and user prompts exist and are non-empty
            if not template.system_prompt.strip():
                logger.error(f"Empty system_prompt in {category}.{prompt_type}")
                return False
            
            if not template.user_prompt.strip():
                logger.error(f"Empty user_prompt in {category}.{prompt_type}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating prompt structure {category}.{prompt_type}: {e}")
            return False
    
    def get_prompt_info(self) -> Dict[str, Any]:
        """
        Get information about loaded prompts.
        
        Returns:
            Dictionary with prompt statistics and metadata
        """
        info = {
            'categories_count': len(self.prompts),
            'last_loaded': self.last_loaded.isoformat() if self.last_loaded else None,
            'prompts_directory': str(self.prompts_directory),
            'categories': {}
        }
        
        for category, category_data in self.prompts.items():
            info['categories'][category] = {
                'types_count': len(category_data),
                'types': list(category_data.keys())
            }
        
        return info


# Global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def initialize_prompt_manager(prompts_directory: str = "prompts") -> PromptManager:
    """Initialize the global prompt manager with a specific directory."""
    global _prompt_manager
    _prompt_manager = PromptManager(prompts_directory)
    return _prompt_manager