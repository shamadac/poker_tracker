"""
Multi-platform poker hand history parser service.

This module provides a comprehensive hand parsing system that supports multiple
poker platforms (PokerStars, GGPoker) with automatic platform detection and
extensible architecture for adding new platforms.
"""
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import logging

from ..schemas.hand import HandCreate, DetailedAction, HandResult, TournamentInfo, CashGameInfo, PlayerStack, TimebankInfo
from .hand_validator import HandValidator, HandParsingErrorHandler, validate_hands_batch

logger = logging.getLogger(__name__)


from .exceptions import HandParsingError, UnsupportedPlatformError


class AbstractHandParser(ABC):
    """Abstract base class for platform-specific hand parsers."""
    
    def __init__(self, player_username: Optional[str] = None):
        """
        Initialize parser with optional player username.
        
        Args:
            player_username: Username to focus parsing on (optional)
        """
        self.player_username = player_username
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name this parser handles."""
        pass
    
    @abstractmethod
    def can_parse(self, content: str) -> bool:
        """
        Check if this parser can handle the given content.
        
        Args:
            content: Raw hand history content
            
        Returns:
            True if this parser can handle the content
        """
        pass
    
    @abstractmethod
    def parse_hands(self, content: str) -> List[HandCreate]:
        """
        Parse hand history content into structured hand data.
        
        Args:
            content: Raw hand history file content
            
        Returns:
            List of parsed hands
            
        Raises:
            HandParsingError: If parsing fails
        """
        pass
    
    def validate_hand(self, hand: HandCreate) -> bool:
        """
        Validate parsed hand data for integrity.
        
        Args:
            hand: Parsed hand data
            
        Returns:
            True if hand data is valid
        """
        try:
            # Basic validation
            if not hand.hand_id or not hand.platform:
                return False
            
            # Validate platform matches this parser
            if hand.platform != self.platform_name:
                return False
            
            # Validate card formats if present
            if hand.player_cards:
                for card in hand.player_cards:
                    if not self._is_valid_card(card):
                        return False
            
            if hand.board_cards:
                for card in hand.board_cards:
                    if not self._is_valid_card(card):
                        return False
            
            # Validate numeric values
            if hand.pot_size is not None and hand.pot_size < 0:
                return False
            
            if hand.rake is not None and hand.rake < 0:
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Hand validation failed: {e}")
            return False
    
    def _is_valid_card(self, card: str) -> bool:
        """
        Validate card format (e.g., 'As', 'Kh', '2c', 'Td').
        
        Args:
            card: Card string to validate
            
        Returns:
            True if card format is valid
        """
        if not card or len(card) != 2:
            return False
        
        rank, suit = card[0], card[1]
        valid_ranks = '23456789TJQKA'
        valid_suits = 'shdc'
        
        return rank in valid_ranks and suit in valid_suits
    
    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """
        Safely parse decimal value from string.
        
        Args:
            value: String value to parse
            
        Returns:
            Decimal value or None if parsing fails
        """
        if not value:
            return None
        
        try:
            # Remove currency symbols and whitespace
            cleaned = re.sub(r'[$€£¥,\s]', '', value)
            return Decimal(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
    
    def _parse_datetime(self, date_str: str, timezone: str = 'UTC') -> Optional[datetime]:
        """
        Parse datetime from various formats.
        
        Args:
            date_str: Date string to parse
            timezone: Timezone string
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        if not date_str:
            return None
        
        # Common poker platform date formats
        formats = [
            '%Y/%m/%d %H:%M:%S',  # PokerStars format
            '%Y-%m-%d %H:%M:%S',  # ISO format
            '%m/%d/%Y %H:%M:%S',  # US format
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse datetime: {date_str}")
        return None


class PlatformDetector:
    """Utility class for detecting poker platform from hand history content."""
    
    @staticmethod
    def detect_platform(content: str) -> str:
        """
        Detect poker platform from hand history content.
        
        Args:
            content: Raw hand history content
            
        Returns:
            Platform name ('pokerstars' or 'ggpoker')
            
        Raises:
            UnsupportedPlatformError: If platform cannot be detected
        """
        if not content:
            raise UnsupportedPlatformError("Empty content provided")
        
        # PokerStars detection patterns
        pokerstars_patterns = [
            r'PokerStars Hand #',
            r'PokerStars Game #',
            r'PokerStars Tournament #',
            r'PokerStars Zoom Hand #'
        ]
        
        # GGPoker detection patterns
        ggpoker_patterns = [
            r'GGPoker Hand #',
            r'GG Poker Hand #',
            r'GGNetwork Hand #'
        ]
        
        # Check for PokerStars
        for pattern in pokerstars_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return 'pokerstars'
        
        # Check for GGPoker
        for pattern in ggpoker_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return 'ggpoker'
        
        # Additional heuristics based on content structure
        if 'Dealt to' in content and 'Total pot' in content:
            # This looks like a poker hand, try to determine platform
            if 'ET' in content or 'UTC' in content:
                return 'pokerstars'  # PokerStars commonly uses these timezones
            elif 'GMT' in content:
                return 'ggpoker'  # GGPoker commonly uses GMT
        
        raise UnsupportedPlatformError(
            "Could not detect poker platform. Supported platforms: PokerStars, GGPoker"
        )


class HandParserService:
    """
    Main service class for parsing poker hand histories from multiple platforms.
    
    This service automatically detects the platform and uses the appropriate
    parser to extract structured data from hand history files.
    """
    
    def __init__(self):
        """Initialize the hand parser service with all available parsers."""
        self.parsers: Dict[str, AbstractHandParser] = {}
        self.detector = PlatformDetector()
        self.validator = HandValidator()
        self.error_handler = HandParsingErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Register parsers (will be implemented in subsequent tasks)
        self._register_parsers()
    
    def _register_parsers(self):
        """Register all available platform parsers."""
        # Import and register PokerStars parser
        try:
            from .pokerstars_parser import PokerStarsParser
            self.parsers['pokerstars'] = PokerStarsParser()
            self.logger.info("Registered PokerStars parser")
        except ImportError as e:
            self.logger.warning(f"Could not import PokerStars parser: {e}")
        
        # Import and register GGPoker parser
        try:
            from .ggpoker_parser import GGPokerParser
            self.parsers['ggpoker'] = GGPokerParser()
            self.logger.info("Registered GGPoker parser")
        except ImportError as e:
            self.logger.warning(f"Could not import GGPoker parser: {e}")
    
    def register_parser(self, parser: AbstractHandParser):
        """
        Register a new platform parser.
        
        Args:
            parser: Parser instance to register
        """
        self.parsers[parser.platform_name] = parser
        self.logger.info(f"Registered parser for platform: {parser.platform_name}")
    
    def get_supported_platforms(self) -> List[str]:
        """
        Get list of supported platforms.
        
        Returns:
            List of supported platform names
        """
        return list(self.parsers.keys())
    
    def detect_platform(self, content: str) -> str:
        """
        Detect platform from hand history content.
        
        Args:
            content: Raw hand history content
            
        Returns:
            Detected platform name
            
        Raises:
            UnsupportedPlatformError: If platform cannot be detected
        """
        return self.detector.detect_platform(content)
    
    def parse_file(self, file_path: Union[str, Path], player_username: Optional[str] = None, 
                   strict_validation: bool = False) -> Tuple[List[HandCreate], List[Dict[str, Any]]]:
        """
        Parse a hand history file with comprehensive error handling.
        
        Args:
            file_path: Path to hand history file
            player_username: Optional username to focus parsing on
            strict_validation: Whether to use strict validation rules
            
        Returns:
            Tuple of (parsed_hands, error_details)
            
        Raises:
            HandParsingError: If file cannot be read or parsed
            UnsupportedPlatformError: If platform is not supported
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise HandParsingError(f"File not found: {file_path}")
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            return self.parse_content(content, player_username, strict_validation)
            
        except Exception as e:
            error_record = self.error_handler.handle_parsing_error(
                e, context={'file_path': str(file_path)}
            )
            self.logger.error(f"Failed to parse file {file_path}: {e}")
            raise HandParsingError(f"Failed to parse file: {e}")
    
    def parse_content(self, content: str, player_username: Optional[str] = None, 
                     strict_validation: bool = False) -> Tuple[List[HandCreate], List[Dict[str, Any]]]:
        """
        Parse hand history content with comprehensive validation and error handling.
        
        Args:
            content: Raw hand history content
            player_username: Optional username to focus parsing on
            strict_validation: Whether to use strict validation rules
            
        Returns:
            Tuple of (valid_hands, error_details)
            
        Raises:
            HandParsingError: If content cannot be parsed
            UnsupportedPlatformError: If platform is not supported
        """
        if not content.strip():
            return [], []
        
        try:
            # Detect platform
            platform = self.detect_platform(content)
            
            # Get appropriate parser
            if platform not in self.parsers:
                raise UnsupportedPlatformError(f"No parser available for platform: {platform}")
            
            parser = self.parsers[platform]
            
            # Set player username if provided
            if player_username:
                parser.player_username = player_username
            
            # Parse hands
            try:
                hands = parser.parse_hands(content)
            except Exception as e:
                error_record = self.error_handler.handle_parsing_error(
                    e, content[:500], {'platform': platform, 'player_username': player_username}
                )
                raise HandParsingError(f"Failed to parse {platform} content: {e}")
            
            # Validate parsed hands
            valid_hands, error_details = validate_hands_batch(hands, strict_validation)
            
            self.logger.info(
                f"Parsed {len(valid_hands)} valid hands from {platform} content "
                f"({len(error_details)} errors/duplicates)"
            )
            
            return valid_hands, error_details
            
        except Exception as e:
            if not isinstance(e, (HandParsingError, UnsupportedPlatformError)):
                error_record = self.error_handler.handle_parsing_error(
                    e, content[:500], {'player_username': player_username}
                )
            raise
    
    def validate_hands(self, hands: List[HandCreate], strict: bool = False) -> Tuple[List[HandCreate], List[Dict[str, Any]]]:
        """
        Validate a list of parsed hands and return only valid ones with error details.
        
        Args:
            hands: List of parsed hands to validate
            strict: Whether to use strict validation rules
            
        Returns:
            Tuple of (valid_hands, error_details)
        """
        return validate_hands_batch(hands, strict)
    
    def get_parsing_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive parsing statistics.
        
        Returns:
            Dictionary with parsing statistics
        """
        return {
            'supported_platforms': self.get_supported_platforms(),
            'duplicate_stats': self.validator.get_duplicate_stats(),
            'error_summary': self.error_handler.get_error_summary(),
            'parsers_registered': len(self.parsers)
        }
    
    def reset_session_data(self):
        """Reset session-specific data (duplicates, errors)."""
        self.validator.reset_duplicate_tracking()
        self.error_handler.clear_error_history()
        self.logger.info("Reset parsing session data")
    
    def get_default_paths(self, platform: str) -> List[str]:
        """
        Get default hand history paths for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            List of default paths for the platform
        """
        import os
        
        paths = []
        
        if platform == 'pokerstars':
            if os.name == 'nt':  # Windows
                base_path = os.path.expandvars(r'%LOCALAPPDATA%\PokerStars\HandHistory')
                if os.path.exists(base_path):
                    # Look for username directories
                    for item in os.listdir(base_path):
                        user_path = os.path.join(base_path, item)
                        if os.path.isdir(user_path):
                            paths.append(user_path)
            else:  # macOS/Linux
                home = os.path.expanduser('~')
                mac_path = os.path.join(home, 'Library/Application Support/PokerStars/HandHistory')
                linux_path = os.path.join(home, '.wine/drive_c/users', os.getenv('USER', 'user'), 
                                        'Local Settings/Application Data/PokerStars/HandHistory')
                
                for path in [mac_path, linux_path]:
                    if os.path.exists(path):
                        for item in os.listdir(path):
                            user_path = os.path.join(path, item)
                            if os.path.isdir(user_path):
                                paths.append(user_path)
        
        elif platform == 'ggpoker':
            if os.name == 'nt':  # Windows
                base_path = os.path.expandvars(r'%APPDATA%\GGPoker\HandHistory')
                if os.path.exists(base_path):
                    paths.append(base_path)
            else:  # macOS
                home = os.path.expanduser('~')
                mac_path = os.path.join(home, 'Library/Application Support/GGPoker/HandHistory')
                if os.path.exists(mac_path):
                    paths.append(mac_path)
        
        return paths
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        Scan directory for hand history files.
        
        Args:
            directory_path: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of hand history file paths
        """
        directory = Path(directory_path)
        
        if not directory.exists() or not directory.is_dir():
            return []
        
        hand_files = []
        
        # Common hand history file extensions
        extensions = ['.txt', '.log']
        
        if recursive:
            for ext in extensions:
                hand_files.extend(directory.rglob(f'*{ext}'))
        else:
            for ext in extensions:
                hand_files.extend(directory.glob(f'*{ext}'))
        
        # Filter files that look like hand histories
        valid_files = []
        for file_path in hand_files:
            try:
                # Quick check if file contains poker hand data
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(1000)  # Read first 1KB
                    if any(pattern in sample for pattern in ['Hand #', 'Dealt to', 'Total pot']):
                        valid_files.append(str(file_path))
            except Exception:
                continue
        
        return valid_files