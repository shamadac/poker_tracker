"""Parse PokerStars hand history files."""
import re
from typing import Dict, List, Optional


class HandParser:
    """Parse PokerStars hand history format."""
    
    def __init__(self, player_username: str):
        self.player_username = player_username
    
    def parse_file(self, filepath: str) -> List[Dict]:
        """Parse a hand history file and return list of hands."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into individual hands
        hands = content.split('\n\n\n')
        parsed_hands = []
        
        for hand_text in hands:
            if hand_text.strip():
                parsed = self.parse_hand(hand_text)
                if parsed:
                    parsed_hands.append(parsed)
        
        return parsed_hands
    
    def parse_hand(self, hand_text: str) -> Optional[Dict]:
        """Parse a single hand history."""
        if not hand_text.strip():
            return None
        
        hand_data = {
            'raw_text': hand_text,
            'hand_id': self._extract_hand_id(hand_text),
            'game_type': self._extract_game_type(hand_text),
            'stakes': self._extract_stakes(hand_text),
            'player_position': self._extract_player_position(hand_text),
            'player_cards': self._extract_player_cards(hand_text),
            'actions': self._extract_actions(hand_text),
            'result': self._extract_result(hand_text),
            'board_cards': self._extract_board_cards(hand_text),
            'pot_size': self._extract_pot_size(hand_text),
            'players': self._extract_players(hand_text),
            'betting_rounds': self._extract_betting_rounds(hand_text),
            'showdown': self._extract_showdown(hand_text)
        }
        
        return hand_data
    
    def _extract_hand_id(self, text: str) -> str:
        match = re.search(r'Hand #(\d+)', text)
        return match.group(1) if match else 'unknown'
    
    def _extract_game_type(self, text: str) -> str:
        match = re.search(r"PokerStars Hand #\d+:\s+([^:]+):", text)
        return match.group(1).strip() if match else 'unknown'
    
    def _extract_stakes(self, text: str) -> str:
        match = re.search(r'\((\$[\d.]+/\$[\d.]+)\)', text)
        return match.group(1) if match else 'unknown'
    
    def _extract_player_position(self, text: str) -> str:
        # Look for player's seat and button position
        player_match = re.search(rf'Seat \d+: {self.player_username}', text)
        button_match = re.search(r'Seat #(\d+) is the button', text)
        
        if player_match and button_match:
            return 'found'
        return 'unknown'
    
    def _extract_player_cards(self, text: str) -> str:
        match = re.search(rf'Dealt to {self.player_username} \[([^\]]+)\]', text)
        return match.group(1) if match else 'unknown'
    
    def _extract_actions(self, text: str) -> List[str]:
        """Extract player's actions in the hand."""
        actions = []
        pattern = rf'{self.player_username}: (folds|checks|calls|bets|raises|all-in).*'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            actions.append(match.group(0))
        
        return actions
    
    def _extract_result(self, text: str) -> str:
        """Extract hand result for player."""
        if f'{self.player_username} collected' in text:
            match = re.search(rf'{self.player_username} collected \$?([\d.]+)', text)
            return f'won ${match.group(1)}' if match else 'won'
        elif f'{self.player_username}: shows' in text and 'won' not in text:
            return 'lost'
        elif f'{self.player_username}: folds' in text:
            return 'folded'
        return 'unknown'

    
    def _extract_board_cards(self, text: str) -> Dict[str, str]:
        """Extract community cards by street."""
        board = {'flop': '', 'turn': '', 'river': ''}
        
        flop_match = re.search(r'\*\*\* FLOP \*\*\* \[([^\]]+)\]', text)
        if flop_match:
            board['flop'] = flop_match.group(1)
        
        turn_match = re.search(r'\*\*\* TURN \*\*\* \[[^\]]+\] \[([^\]]+)\]', text)
        if turn_match:
            board['turn'] = turn_match.group(1)
        
        river_match = re.search(r'\*\*\* RIVER \*\*\* \[[^\]]+\] \[([^\]]+)\]', text)
        if river_match:
            board['river'] = river_match.group(1)
        
        return board
    
    def _extract_pot_size(self, text: str) -> str:
        """Extract total pot size."""
        match = re.search(r'Total pot \$?([\d.]+)', text)
        return match.group(1) if match else '0'
    
    def _extract_players(self, text: str) -> List[Dict]:
        """Extract all players and their stack sizes."""
        players = []
        pattern = r'Seat (\d+): ([^\(]+) \(\$?([\d.]+) in chips\)'
        
        for match in re.finditer(pattern, text):
            players.append({
                'seat': match.group(1),
                'name': match.group(2).strip(),
                'stack': match.group(3)
            })
        
        return players
    
    def _extract_betting_rounds(self, text: str) -> Dict[str, List[str]]:
        """Extract betting actions by street."""
        rounds = {
            'preflop': [],
            'flop': [],
            'turn': [],
            'river': []
        }
        
        # Split by streets
        sections = text.split('***')
        current_street = 'preflop'
        
        for section in sections:
            if 'HOLE CARDS' in section:
                current_street = 'preflop'
                actions = section.split('\n')
            elif 'FLOP' in section:
                current_street = 'flop'
                actions = section.split('\n')
            elif 'TURN' in section:
                current_street = 'turn'
                actions = section.split('\n')
            elif 'RIVER' in section:
                current_street = 'river'
                actions = section.split('\n')
            else:
                continue
            
            for action in actions:
                if any(word in action for word in ['folds', 'checks', 'calls', 'bets', 'raises', 'all-in']):
                    rounds[current_street].append(action.strip())
        
        return rounds
    
    def _extract_showdown(self, text: str) -> List[Dict]:
        """Extract showdown information."""
        showdown = []
        
        if '*** SHOW DOWN ***' in text:
            pattern = r'([^:]+): shows \[([^\]]+)\]'
            for match in re.finditer(pattern, text):
                showdown.append({
                    'player': match.group(1).strip(),
                    'cards': match.group(2)
                })
        
        return showdown
