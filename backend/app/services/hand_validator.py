"""
Hand parsing validation and error handling utilities.

This module provides comprehensive validation for parsed hand data,
duplicate detection, and error handling for the hand parsing system.
"""
import hashlib
import logging
from typing import List, Dict, Set, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, timedelta

from ..schemas.hand import HandCreate, DetailedAction, HandResult
from .exceptions import HandParsingError, UnsupportedPlatformError


class ValidationError(HandParsingError):
    """Exception raised when hand validation fails."""
    pass


class DuplicateHandError(HandParsingError):
    """Exception raised when duplicate hands are detected."""
    pass


class HandValidator:
    """Comprehensive hand validation and duplicate detection."""
    
    def __init__(self):
        """Initialize the hand validator."""
        self.logger = logging.getLogger(__name__)
        self._seen_hands: Set[str] = set()
        self._hand_hashes: Dict[str, str] = {}
    
    def validate_hand(self, hand: HandCreate, strict: bool = False) -> Tuple[bool, List[str]]:
        """
        Validate a parsed hand for data integrity.
        
        Args:
            hand: Parsed hand data to validate
            strict: Whether to use strict validation rules
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Basic required field validation
            basic_errors = self._validate_basic_fields(hand)
            errors.extend(basic_errors)
            
            # Card validation
            card_errors = self._validate_cards(hand)
            errors.extend(card_errors)
            
            # Financial data validation
            financial_errors = self._validate_financial_data(hand)
            errors.extend(financial_errors)
            
            # Action sequence validation
            action_errors = self._validate_actions(hand)
            errors.extend(action_errors)
            
            # Position and seat validation
            position_errors = self._validate_positions(hand)
            errors.extend(position_errors)
            
            # Game format specific validation
            format_errors = self._validate_game_format(hand)
            errors.extend(format_errors)
            
            # Strict validation (optional)
            if strict:
                strict_errors = self._validate_strict_rules(hand)
                errors.extend(strict_errors)
            
            is_valid = len(errors) == 0
            
            if not is_valid:
                self.logger.warning(f"Hand {hand.hand_id} validation failed: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            self.logger.error(f"Error during hand validation: {e}")
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_basic_fields(self, hand: HandCreate) -> List[str]:
        """Validate basic required fields."""
        errors = []
        
        if not hand.hand_id:
            errors.append("Hand ID is required")
        elif not hand.hand_id.isdigit():
            errors.append("Hand ID must be numeric")
        
        if not hand.platform:
            errors.append("Platform is required")
        elif hand.platform not in ['pokerstars', 'ggpoker']:
            errors.append(f"Unsupported platform: {hand.platform}")
        
        if hand.game_format and hand.game_format not in ['tournament', 'cash', 'sng']:
            errors.append(f"Invalid game format: {hand.game_format}")
        
        return errors
    
    def _validate_cards(self, hand: HandCreate) -> List[str]:
        """Validate card formats and consistency."""
        errors = []
        
        # Validate player cards
        if hand.player_cards:
            for i, card in enumerate(hand.player_cards):
                if not self._is_valid_card_format(card):
                    errors.append(f"Invalid player card format at position {i}: {card}")
        
        # Validate board cards
        if hand.board_cards:
            if len(hand.board_cards) > 5:
                errors.append(f"Too many board cards: {len(hand.board_cards)}")
            
            for i, card in enumerate(hand.board_cards):
                if not self._is_valid_card_format(card):
                    errors.append(f"Invalid board card format at position {i}: {card}")
        
        # Check for duplicate cards
        all_cards = []
        if hand.player_cards:
            all_cards.extend(hand.player_cards)
        if hand.board_cards:
            all_cards.extend(hand.board_cards)
        
        if len(all_cards) != len(set(all_cards)):
            errors.append("Duplicate cards detected in hand")
        
        return errors
    
    def _is_valid_card_format(self, card: str) -> bool:
        """Validate individual card format."""
        if not card or len(card) != 2:
            return False
        
        rank, suit = card[0], card[1]
        valid_ranks = '23456789TJQKA'
        valid_suits = 'shdc'
        
        return rank in valid_ranks and suit in valid_suits
    
    def _validate_financial_data(self, hand: HandCreate) -> List[str]:
        """Validate financial data consistency."""
        errors = []
        
        # Validate pot size
        if hand.pot_size is not None:
            if hand.pot_size < 0:
                errors.append("Pot size cannot be negative")
            elif hand.pot_size == 0 and hand.result and hand.result.result == 'won':
                errors.append("Won hand cannot have zero pot size")
        
        # Validate rake
        if hand.rake is not None:
            if hand.rake < 0:
                errors.append("Rake cannot be negative")
            elif hand.pot_size and hand.rake > hand.pot_size:
                errors.append("Rake cannot exceed pot size")
        
        # Validate jackpot contribution
        if hand.jackpot_contribution is not None and hand.jackpot_contribution < 0:
            errors.append("Jackpot contribution cannot be negative")
        
        # Validate blinds
        if hand.blinds:
            if 'small' in hand.blinds and hand.blinds['small'] < 0:
                errors.append("Small blind cannot be negative")
            if 'big' in hand.blinds and hand.blinds['big'] < 0:
                errors.append("Big blind cannot be negative")
            if ('small' in hand.blinds and 'big' in hand.blinds and 
                hand.blinds['small'] >= hand.blinds['big']):
                errors.append("Small blind must be less than big blind")
        
        return errors
    
    def _validate_actions(self, hand: HandCreate) -> List[str]:
        """Validate action sequence consistency."""
        errors = []
        
        if not hand.actions:
            return errors
        
        # Group actions by street
        streets = ['preflop', 'flop', 'turn', 'river']
        street_actions = {street: [] for street in streets}
        
        for action in hand.actions:
            if action.street in street_actions:
                street_actions[action.street].append(action)
            else:
                errors.append(f"Invalid street in action: {action.street}")
        
        # Validate action sequence for each street
        for street, actions in street_actions.items():
            if actions:
                street_errors = self._validate_street_actions(actions, street)
                errors.extend(street_errors)
        
        return errors
    
    def _validate_street_actions(self, actions: List[DetailedAction], street: str) -> List[str]:
        """Validate actions for a specific street."""
        errors = []
        
        for i, action in enumerate(actions):
            # Validate action type
            valid_actions = ['fold', 'check', 'call', 'bet', 'raise', 'all-in']
            if action.action not in valid_actions:
                errors.append(f"Invalid action type on {street}: {action.action}")
            
            # Validate action amounts
            if action.action in ['bet', 'raise', 'call'] and action.amount is None:
                errors.append(f"Action {action.action} on {street} missing amount")
            elif action.action in ['fold', 'check'] and action.amount is not None:
                errors.append(f"Action {action.action} on {street} should not have amount")
            
            # Validate amount is positive
            if action.amount is not None and action.amount <= 0:
                errors.append(f"Action amount must be positive on {street}")
            
            # Check for fold after fold (player can only fold once)
            if action.action == 'fold' and i < len(actions) - 1:
                errors.append(f"Actions after fold on {street}")
        
        return errors
    
    def _validate_positions(self, hand: HandCreate) -> List[str]:
        """Validate position and seat information."""
        errors = []
        
        # Validate seat numbers
        if hand.seat_number is not None:
            if hand.seat_number < 1 or hand.seat_number > 10:
                errors.append(f"Invalid seat number: {hand.seat_number}")
        
        if hand.button_position is not None:
            if hand.button_position < 1 or hand.button_position > 10:
                errors.append(f"Invalid button position: {hand.button_position}")
        
        # Validate table size consistency
        if hand.table_size is not None:
            if hand.table_size < 2 or hand.table_size > 10:
                errors.append(f"Invalid table size: {hand.table_size}")
            
            # Check seat numbers are within table size
            if hand.seat_number and hand.seat_number > hand.table_size:
                errors.append("Seat number exceeds table size")
            
            if hand.button_position and hand.button_position > hand.table_size:
                errors.append("Button position exceeds table size")
        
        # Validate position names
        if hand.position:
            valid_positions = ['UTG', 'UTG+1', 'MP', 'MP+1', 'CO', 'BTN', 'SB', 'BB', 'HJ']
            if not any(pos in hand.position for pos in valid_positions):
                # Allow SEAT{number} format as fallback
                if not hand.position.startswith('SEAT'):
                    errors.append(f"Invalid position: {hand.position}")
        
        return errors
    
    def _validate_game_format(self, hand: HandCreate) -> List[str]:
        """Validate game format specific rules."""
        errors = []
        
        if hand.game_format == 'tournament':
            if not hand.tournament_info:
                errors.append("Tournament hands must have tournament info")
            elif not hand.tournament_info.tournament_id:
                errors.append("Tournament info must have tournament ID")
        
        elif hand.game_format == 'cash':
            if not hand.cash_game_info:
                errors.append("Cash game hands must have cash game info")
            elif not hand.cash_game_info.table_name:
                errors.append("Cash game info must have table name")
        
        return errors
    
    def _validate_strict_rules(self, hand: HandCreate) -> List[str]:
        """Apply strict validation rules."""
        errors = []
        
        # Require player cards for complete hands
        if not hand.player_cards and hand.result and hand.result.result != 'folded':
            errors.append("Non-folded hands should have player cards")
        
        # Require board cards for showdown hands
        if (hand.result and hand.result.showdown and 
            (not hand.board_cards or len(hand.board_cards) < 3)):
            errors.append("Showdown hands should have at least flop cards")
        
        # Validate date is reasonable
        if hand.date_played:
            now = datetime.now()
            if hand.date_played > now:
                errors.append("Hand date cannot be in the future")
            elif hand.date_played < now - timedelta(days=365 * 10):
                errors.append("Hand date is too old (>10 years)")
        
        return errors
    
    def check_duplicate(self, hand: HandCreate) -> bool:
        """
        Check if hand is a duplicate.
        
        Args:
            hand: Hand to check for duplicates
            
        Returns:
            True if hand is a duplicate
        """
        hand_key = f"{hand.platform}:{hand.hand_id}"
        
        if hand_key in self._seen_hands:
            return True
        
        # Also check content hash for near-duplicates
        content_hash = self._calculate_hand_hash(hand)
        if content_hash in self._hand_hashes.values():
            return True
        
        # Record this hand
        self._seen_hands.add(hand_key)
        self._hand_hashes[hand_key] = content_hash
        
        return False
    
    def _calculate_hand_hash(self, hand: HandCreate) -> str:
        """Calculate a hash of hand content for duplicate detection."""
        # Create a string representation of key hand data
        hash_data = [
            hand.platform,
            hand.hand_id,
            str(hand.date_played) if hand.date_played else '',
            hand.game_type or '',
            hand.stakes or '',
            ','.join(hand.player_cards) if hand.player_cards else '',
            ','.join(hand.board_cards) if hand.board_cards else '',
            str(hand.pot_size) if hand.pot_size else '',
            hand.raw_text[:100] if hand.raw_text else ''  # First 100 chars
        ]
        
        content = '|'.join(hash_data)
        return hashlib.md5(content.encode()).hexdigest()
    
    def reset_duplicate_tracking(self):
        """Reset duplicate tracking (useful for new sessions)."""
        self._seen_hands.clear()
        self._hand_hashes.clear()
        self.logger.info("Reset duplicate tracking")
    
    def get_duplicate_stats(self) -> Dict[str, int]:
        """Get statistics about processed hands."""
        return {
            'total_hands_seen': len(self._seen_hands),
            'unique_content_hashes': len(set(self._hand_hashes.values()))
        }


class HandParsingErrorHandler:
    """Centralized error handling for hand parsing operations."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_counts: Dict[str, int] = {}
        self.recent_errors: List[Dict[str, Any]] = []
        self.max_recent_errors = 100
    
    def handle_parsing_error(self, error: Exception, hand_text: str = "", 
                           context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle and log parsing errors with context.
        
        Args:
            error: The exception that occurred
            hand_text: Raw hand text that caused the error
            context: Additional context information
            
        Returns:
            Error information dictionary
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Count error types
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Create error record
        error_record = {
            'timestamp': datetime.now(),
            'error_type': error_type,
            'error_message': error_message,
            'hand_preview': hand_text[:200] if hand_text else '',
            'context': context or {}
        }
        
        # Store recent errors
        self.recent_errors.append(error_record)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Log the error
        self.logger.error(
            f"Hand parsing error [{error_type}]: {error_message}",
            extra={'context': context, 'hand_preview': hand_text[:100]}
        )
        
        return error_record
    
    def should_continue_parsing(self, error_rate_threshold: float = 0.5) -> bool:
        """
        Determine if parsing should continue based on error rate.
        
        Args:
            error_rate_threshold: Maximum acceptable error rate (0.0-1.0)
            
        Returns:
            True if parsing should continue
        """
        if len(self.recent_errors) < 10:
            return True  # Not enough data to determine
        
        # Calculate recent error rate
        recent_window = self.recent_errors[-20:]  # Last 20 operations
        error_rate = len(recent_window) / 20
        
        return error_rate <= error_rate_threshold
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of parsing errors."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': dict(self.error_counts),
            'recent_error_count': len(self.recent_errors),
            'most_common_error': max(self.error_counts.items(), key=lambda x: x[1])[0] if self.error_counts else None
        }
    
    def clear_error_history(self):
        """Clear error tracking history."""
        self.error_counts.clear()
        self.recent_errors.clear()
        self.logger.info("Cleared error tracking history")


def validate_hands_batch(hands: List[HandCreate], strict: bool = False) -> Tuple[List[HandCreate], List[Dict[str, Any]]]:
    """
    Validate a batch of hands and return valid ones with error details.
    
    Args:
        hands: List of hands to validate
        strict: Whether to use strict validation
        
    Returns:
        Tuple of (valid_hands, error_details)
    """
    validator = HandValidator()
    error_handler = HandParsingErrorHandler()
    
    valid_hands = []
    error_details = []
    
    for hand in hands:
        try:
            # Check for duplicates
            if validator.check_duplicate(hand):
                error_details.append({
                    'hand_id': hand.hand_id,
                    'error_type': 'DuplicateHand',
                    'error_message': 'Duplicate hand detected'
                })
                continue
            
            # Validate hand
            is_valid, validation_errors = validator.validate_hand(hand, strict)
            
            if is_valid:
                valid_hands.append(hand)
            else:
                error_details.append({
                    'hand_id': hand.hand_id,
                    'error_type': 'ValidationError',
                    'error_message': '; '.join(validation_errors),
                    'validation_errors': validation_errors
                })
        
        except Exception as e:
            error_record = error_handler.handle_parsing_error(e, hand.raw_text or '', {'hand_id': hand.hand_id})
            error_details.append({
                'hand_id': hand.hand_id,
                'error_type': error_record['error_type'],
                'error_message': error_record['error_message']
            })
    
    return valid_hands, error_details