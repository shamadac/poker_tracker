"""
PokerStars hand history parser implementation.

This module provides comprehensive parsing for PokerStars hand history format,
supporting both cash games and tournaments, play money and real money games.
"""
import re
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from .hand_parser import AbstractHandParser
from .exceptions import HandParsingError
from ..schemas.hand import (
    HandCreate, DetailedAction, HandResult, TournamentInfo, 
    CashGameInfo, PlayerStack, TimebankInfo
)


class PokerStarsParser(AbstractHandParser):
    """Parser for PokerStars hand history format."""
    
    @property
    def platform_name(self) -> str:
        """Return the platform name."""
        return 'pokerstars'
    
    def can_parse(self, content: str) -> bool:
        """Check if content is PokerStars format."""
        pokerstars_patterns = [
            r'PokerStars Hand #',
            r'PokerStars Game #',
            r'PokerStars Tournament #',
            r'PokerStars Zoom Hand #'
        ]
        
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in pokerstars_patterns)
    
    def parse_hands(self, content: str) -> List[HandCreate]:
        """Parse PokerStars hand history content."""
        if not self.can_parse(content):
            raise HandParsingError("Content is not PokerStars format")
        
        # Split content into individual hands
        # Hands are separated by double newlines
        hand_texts = re.split(r'\n\s*\n\s*\n', content.strip())
        
        parsed_hands = []
        for hand_text in hand_texts:
            if hand_text.strip():
                try:
                    hand = self._parse_single_hand(hand_text.strip())
                    if hand:
                        parsed_hands.append(hand)
                except Exception as e:
                    self.logger.warning(f"Failed to parse hand: {e}")
                    continue
        
        self.logger.info(f"Parsed {len(parsed_hands)} hands from PokerStars content")
        return parsed_hands
    
    def _parse_single_hand(self, hand_text: str) -> Optional[HandCreate]:
        """Parse a single hand from PokerStars format."""
        if not hand_text.strip():
            return None
        
        try:
            # Extract basic hand information
            hand_id = self._extract_hand_id(hand_text)
            if not hand_id:
                return None
            
            # Determine if this is a tournament or cash game
            is_tournament = 'Tournament #' in hand_text
            
            hand_data = HandCreate(
                hand_id=hand_id,
                platform='pokerstars',
                game_type=self._extract_game_type(hand_text),
                game_format='tournament' if is_tournament else 'cash',
                stakes=self._extract_stakes(hand_text),
                blinds=self._extract_blinds(hand_text),
                table_size=self._extract_table_size(hand_text),
                date_played=self._extract_date(hand_text),
                player_cards=self._extract_player_cards(hand_text),
                board_cards=self._extract_board_cards(hand_text),
                position=self._extract_position(hand_text),
                seat_number=self._extract_seat_number(hand_text),
                button_position=self._extract_button_position(hand_text),
                actions=self._extract_actions(hand_text),
                result=self._extract_result(hand_text),
                pot_size=self._extract_pot_size(hand_text),
                rake=self._extract_rake(hand_text),
                tournament_info=self._extract_tournament_info(hand_text) if is_tournament else None,
                cash_game_info=self._extract_cash_game_info(hand_text) if not is_tournament else None,
                player_stacks=self._extract_player_stacks(hand_text),
                hand_duration=self._extract_hand_duration(hand_text),
                timezone=self._extract_timezone(hand_text),
                currency=self._extract_currency(hand_text),
                is_play_money=self._is_play_money(hand_text),
                raw_text=hand_text
            )
            
            return hand_data
            
        except Exception as e:
            self.logger.error(f"Error parsing PokerStars hand: {e}")
            raise HandParsingError(f"Failed to parse PokerStars hand: {e}")
    
    def _extract_hand_id(self, text: str) -> Optional[str]:
        """Extract hand ID from PokerStars format."""
        patterns = [
            r'PokerStars Hand #(\d+)',
            r'PokerStars Game #(\d+)',
            r'PokerStars Tournament #\d+, Hand #(\d+)',
            r'PokerStars Zoom Hand #(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_game_type(self, text: str) -> Optional[str]:
        """Extract game type (Hold'em, Omaha, etc.)."""
        match = re.search(r'PokerStars (?:Hand|Game|Tournament) #\d+:\s*([^(]+)', text)
        if match:
            game_type = match.group(1).strip()
            # Clean up common variations
            game_type = re.sub(r'\s+', ' ', game_type)
            return game_type
        return None
    
    def _extract_stakes(self, text: str) -> Optional[str]:
        """Extract stakes information."""
        # Tournament format: Tournament #123456789, $1.00+$0.10 USD
        tournament_match = re.search(r'Tournament #\d+,\s*([^)]+)', text)
        if tournament_match:
            return tournament_match.group(1).strip()
        
        # Cash game format: ($0.02/$0.05 CAD)
        cash_match = re.search(r'\(([^)]+)\)', text)
        if cash_match:
            stakes = cash_match.group(1)
            # Remove currency if present at the end
            stakes = re.sub(r'\s+[A-Z]{3}$', '', stakes)
            return stakes
        
        return None
    
    def _extract_blinds(self, text: str) -> Optional[Dict[str, Decimal]]:
        """Extract blind structure."""
        blinds = {}
        
        # Tournament blinds: (100/200)
        tournament_match = re.search(r'\((\d+)/(\d+)\)', text)
        if tournament_match:
            blinds['small'] = Decimal(tournament_match.group(1))
            blinds['big'] = Decimal(tournament_match.group(2))
        
        # Cash game blinds: ($0.02/$0.05)
        cash_match = re.search(r'\(\$?([\d.]+)/\$?([\d.]+)', text)
        if cash_match:
            blinds['small'] = Decimal(cash_match.group(1))
            blinds['big'] = Decimal(cash_match.group(2))
        
        # Look for ante
        ante_match = re.search(r'ante (\d+)', text, re.IGNORECASE)
        if ante_match:
            blinds['ante'] = Decimal(ante_match.group(1))
        
        return blinds if blinds else None
    
    def _extract_table_size(self, text: str) -> Optional[int]:
        """Extract table size (6-max, 9-max, etc.)."""
        # Look for explicit table size
        size_match = re.search(r'(\d+)-max', text)
        if size_match:
            return int(size_match.group(1))
        
        # Count seats if no explicit size
        seat_matches = re.findall(r'Seat \d+:', text)
        if seat_matches:
            return len(seat_matches)
        
        return None
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract hand date and time."""
        # PokerStars format: 2026/01/14 12:23:34 ET
        match = re.search(r'(\d{4}/\d{2}/\d{2} \d{1,2}:\d{2}:\d{2})', text)
        if match:
            return self._parse_datetime(match.group(1))
        return None
    
    def _extract_timezone(self, text: str) -> Optional[str]:
        """Extract timezone information."""
        match = re.search(r'\d{4}/\d{2}/\d{2} \d{1,2}:\d{2}:\d{2} ([A-Z]{2,3})', text)
        return match.group(1) if match else None
    
    def _extract_currency(self, text: str) -> Optional[str]:
        """Extract currency from stakes."""
        match = re.search(r'\([^)]*\s+([A-Z]{3})\)', text)
        if match:
            return match.group(1)
        
        # Check for USD symbol
        if '$' in text and 'CAD' not in text:
            return 'USD'
        elif 'CAD' in text:
            return 'CAD'
        
        return None
    
    def _is_play_money(self, text: str) -> bool:
        """Determine if this is a play money game."""
        return '(Play Money)' in text
    
    def _extract_player_cards(self, text: str) -> Optional[List[str]]:
        """Extract player's hole cards."""
        if not self.player_username:
            return None
        
        pattern = rf'Dealt to {re.escape(self.player_username)} \[([^\]]+)\]'
        match = re.search(pattern, text)
        if match:
            cards_str = match.group(1)
            # Split cards and clean them
            cards = [card.strip() for card in cards_str.split()]
            return cards
        return None
    
    def _extract_board_cards(self, text: str) -> Optional[List[str]]:
        """Extract community cards."""
        board_cards = []
        
        # Extract flop cards
        flop_match = re.search(r'\*\*\* FLOP \*\*\* \[([^\]]+)\]', text)
        if flop_match:
            flop_cards = [card.strip() for card in flop_match.group(1).split()]
            board_cards.extend(flop_cards)
        
        # Extract turn card
        turn_match = re.search(r'\*\*\* TURN \*\*\* \[[^\]]+\] \[([^\]]+)\]', text)
        if turn_match:
            turn_card = turn_match.group(1).strip()
            board_cards.append(turn_card)
        
        # Extract river card
        river_match = re.search(r'\*\*\* RIVER \*\*\* \[[^\]]+\] \[([^\]]+)\]', text)
        if river_match:
            river_card = river_match.group(1).strip()
            board_cards.append(river_card)
        
        return board_cards if board_cards else None
    
    def _extract_position(self, text: str) -> Optional[str]:
        """Extract player's position."""
        if not self.player_username:
            return None
        
        # Find player's seat
        player_seat_match = re.search(rf'Seat (\d+): {re.escape(self.player_username)}', text)
        if not player_seat_match:
            return None
        
        player_seat = int(player_seat_match.group(1))
        
        # Find button position
        button_match = re.search(r'Seat #(\d+) is the button', text)
        if not button_match:
            return None
        
        button_seat = int(button_match.group(1))
        
        # Count total seats
        seat_matches = re.findall(r'Seat \d+:', text)
        total_seats = len(seat_matches)
        
        # Calculate position relative to button
        position_map = self._calculate_position(player_seat, button_seat, total_seats)
        return position_map
    
    def _calculate_position(self, player_seat: int, button_seat: int, total_seats: int) -> str:
        """Calculate position based on seat numbers."""
        # Calculate seats after button
        if player_seat > button_seat:
            seats_after_button = player_seat - button_seat
        else:
            seats_after_button = (total_seats - button_seat) + player_seat
        
        # Map to position names
        if total_seats <= 2:
            return 'BTN' if player_seat == button_seat else 'BB'
        elif total_seats <= 6:
            position_map = {
                0: 'BTN',
                1: 'SB',
                2: 'BB',
                3: 'UTG',
                4: 'MP' if total_seats == 6 else 'CO',
                5: 'CO'
            }
        else:  # 7+ seats
            position_map = {
                0: 'BTN',
                1: 'SB',
                2: 'BB',
                3: 'UTG',
                4: 'UTG+1',
                5: 'MP',
                6: 'MP+1' if total_seats > 8 else 'CO',
                7: 'CO',
                8: 'HJ'
            }
        
        return position_map.get(seats_after_button, f'SEAT{player_seat}')
    
    def _extract_seat_number(self, text: str) -> Optional[int]:
        """Extract player's seat number."""
        if not self.player_username:
            return None
        
        match = re.search(rf'Seat (\d+): {re.escape(self.player_username)}', text)
        return int(match.group(1)) if match else None
    
    def _extract_button_position(self, text: str) -> Optional[int]:
        """Extract button seat number."""
        match = re.search(r'Seat #(\d+) is the button', text)
        return int(match.group(1)) if match else None
    
    def _extract_actions(self, text: str) -> Optional[List[DetailedAction]]:
        """Extract detailed action sequence."""
        if not self.player_username:
            return None
        
        actions = []
        
        # Split text by streets
        streets = ['preflop', 'flop', 'turn', 'river']
        street_sections = self._split_by_streets(text)
        
        for street, section in street_sections.items():
            if section and street in streets:
                street_actions = self._extract_street_actions(section, street)
                actions.extend(street_actions)
        
        return actions if actions else None
    
    def _split_by_streets(self, text: str) -> Dict[str, str]:
        """Split hand text by betting streets."""
        sections = {}
        
        # Find street markers
        street_patterns = {
            'preflop': r'\*\*\* HOLE CARDS \*\*\*(.*?)(?=\*\*\*|$)',
            'flop': r'\*\*\* FLOP \*\*\*.*?\](.*?)(?=\*\*\*|$)',
            'turn': r'\*\*\* TURN \*\*\*.*?\](.*?)(?=\*\*\*|$)',
            'river': r'\*\*\* RIVER \*\*\*.*?\](.*?)(?=\*\*\*|$)'
        }
        
        for street, pattern in street_patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                sections[street] = match.group(1).strip()
        
        return sections
    
    def _extract_street_actions(self, section: str, street: str) -> List[DetailedAction]:
        """Extract actions from a specific street."""
        actions = []
        
        if not self.player_username:
            return actions
        
        # Pattern to match player actions
        action_pattern = rf'{re.escape(self.player_username)}: (folds|checks|calls|bets|raises)(?:\s+\$?([\d.]+))?(?:\s+to\s+\$?([\d.]+))?(?:\s+and\s+is\s+all-in)?'
        
        for match in re.finditer(action_pattern, section):
            action_type = match.group(1)
            amount1 = match.group(2)
            amount2 = match.group(3)
            
            # Determine action amount
            amount = None
            if amount2:  # Raise to amount
                amount = self._parse_decimal(amount2)
            elif amount1:  # Bet/call amount
                amount = self._parse_decimal(amount1)
            
            # Check if all-in
            is_all_in = 'all-in' in match.group(0)
            
            action = DetailedAction(
                player=self.player_username,
                action=action_type,
                amount=amount,
                street=street,
                position=self._extract_position(section) or 'unknown',
                is_all_in=is_all_in,
                stack_after=Decimal('0')  # Would need more parsing to get exact stack
            )
            
            actions.append(action)
        
        return actions
    
    def _extract_result(self, text: str) -> Optional[HandResult]:
        """Extract hand result."""
        if not self.player_username:
            return None
        
        # Check if player won
        won_pattern = rf'{re.escape(self.player_username)} collected \$?([\d.]+)'
        won_match = re.search(won_pattern, text)
        if won_match:
            amount = self._parse_decimal(won_match.group(1))
            return HandResult(
                result='won',
                amount_won=amount,
                showdown='SHOW DOWN' in text
            )
        
        # Check if player showed cards (usually means they lost or split)
        show_pattern = rf'{re.escape(self.player_username)}: shows'
        if re.search(show_pattern, text):
            return HandResult(
                result='lost',
                showdown=True
            )
        
        # Check if player folded
        fold_pattern = rf'{re.escape(self.player_username)}: folds'
        if re.search(fold_pattern, text):
            return HandResult(
                result='folded',
                showdown=False
            )
        
        return None
    
    def _extract_pot_size(self, text: str) -> Optional[Decimal]:
        """Extract total pot size."""
        match = re.search(r'Total pot \$?([\d.]+)', text)
        return self._parse_decimal(match.group(1)) if match else None
    
    def _extract_rake(self, text: str) -> Optional[Decimal]:
        """Extract rake amount."""
        match = re.search(r'Rake \$?([\d.]+)', text)
        return self._parse_decimal(match.group(1)) if match else None
    
    def _extract_tournament_info(self, text: str) -> Optional[TournamentInfo]:
        """Extract tournament-specific information."""
        # Tournament ID
        tournament_match = re.search(r'Tournament #(\d+)', text)
        if not tournament_match:
            return None
        
        tournament_id = tournament_match.group(1)
        
        # Buy-in information
        buyin_match = re.search(r'Tournament #\d+,\s*\$?([\d.]+)\+\$?([\d.]+)', text)
        buy_in = None
        if buyin_match:
            buy_in = Decimal(buyin_match.group(1)) + Decimal(buyin_match.group(2))
        
        # Level information (if available)
        level_match = re.search(r'Level (\d+)', text)
        level = int(level_match.group(1)) if level_match else None
        
        return TournamentInfo(
            tournament_id=tournament_id,
            buy_in=buy_in,
            level=level
        )
    
    def _extract_cash_game_info(self, text: str) -> Optional[CashGameInfo]:
        """Extract cash game-specific information."""
        # Table name
        table_match = re.search(r"Table '([^']+)'", text)
        if not table_match:
            return None
        
        table_name = table_match.group(1)
        
        # Table type (6-max, 9-max, etc.)
        max_players = self._extract_table_size(text)
        
        return CashGameInfo(
            table_name=table_name,
            max_players=max_players
        )
    
    def _extract_player_stacks(self, text: str) -> Optional[List[PlayerStack]]:
        """Extract all player stack information."""
        stacks = []
        
        # Pattern to match seat information
        pattern = r'Seat (\d+): ([^(]+) \((\$?[\d.]+) in chips\)'
        
        for match in re.finditer(pattern, text):
            seat_num = int(match.group(1))
            player_name = match.group(2).strip()
            stack_str = match.group(3)
            
            # Parse stack amount
            stack_amount = self._parse_decimal(stack_str)
            if stack_amount is not None:
                stack = PlayerStack(
                    player_name=player_name,
                    seat_number=seat_num,
                    stack_size=stack_amount,
                    is_sitting_out='is sitting out' in match.group(0)
                )
                stacks.append(stack)
        
        return stacks if stacks else None
    
    def _extract_hand_duration(self, text: str) -> Optional[int]:
        """Extract hand duration if available."""
        # PokerStars doesn't typically include hand duration in standard format
        # This would need to be calculated from timestamps if available
        return None