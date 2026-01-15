"""Comprehensive playstyle analysis."""
from typing import List, Dict
from collections import defaultdict


class PlaystyleAnalyzer:
    """Analyze overall playstyle from multiple hands."""
    
    def __init__(self, player_username: str):
        self.player_username = player_username
    
    def analyze_playstyle(self, hands: List[Dict]) -> Dict:
        """Generate comprehensive playstyle report."""
        if not hands:
            return {}
        
        stats = {
            'total_hands': len(hands),
            'vpip': self._calculate_vpip(hands),
            'pfr': self._calculate_pfr(hands),
            'aggression': self._calculate_aggression(hands),
            'win_rate': self._calculate_win_rate(hands),
            'position_stats': self._analyze_positions(hands),
            'common_mistakes': self._identify_mistakes(hands),
            'strengths': self._identify_strengths(hands)
        }
        
        return stats
    
    def _calculate_vpip(self, hands: List[Dict]) -> float:
        """Calculate Voluntarily Put money In Pot percentage."""
        voluntary_hands = 0
        
        for hand in hands:
            actions = hand.get('actions', [])
            for action in actions:
                if 'calls' in action or 'raises' in action or 'bets' in action:
                    voluntary_hands += 1
                    break
        
        return round((voluntary_hands / len(hands)) * 100, 1) if hands else 0
    
    def _calculate_pfr(self, hands: List[Dict]) -> float:
        """Calculate Pre-Flop Raise percentage."""
        pfr_hands = 0
        
        for hand in hands:
            betting = hand.get('betting_rounds', {})
            preflop = betting.get('preflop', [])
            
            for action in preflop:
                if self.player_username in action and 'raises' in action:
                    pfr_hands += 1
                    break
        
        return round((pfr_hands / len(hands)) * 100, 1) if hands else 0
    
    def _calculate_aggression(self, hands: List[Dict]) -> float:
        """Calculate aggression factor (bets+raises / calls)."""
        aggressive_actions = 0
        passive_actions = 0
        
        for hand in hands:
            actions = hand.get('actions', [])
            for action in actions:
                if 'bets' in action or 'raises' in action:
                    aggressive_actions += 1
                elif 'calls' in action:
                    passive_actions += 1
        
        if passive_actions == 0:
            return aggressive_actions
        
        return round(aggressive_actions / passive_actions, 2)
    
    def _calculate_win_rate(self, hands: List[Dict]) -> Dict:
        """Calculate win/loss statistics."""
        wins = 0
        losses = 0
        folds = 0
        
        for hand in hands:
            result = hand.get('result', '')
            if 'won' in result:
                wins += 1
            elif 'lost' in result:
                losses += 1
            elif 'folded' in result:
                folds += 1
        
        return {
            'wins': wins,
            'losses': losses,
            'folds': folds,
            'win_percentage': round((wins / len(hands)) * 100, 1) if hands else 0
        }
    
    def _analyze_positions(self, hands: List[Dict]) -> Dict:
        """Analyze play by position."""
        positions = defaultdict(lambda: {'hands': 0, 'wins': 0})
        
        for hand in hands:
            pos = hand.get('player_position', 'unknown')
            positions[pos]['hands'] += 1
            if 'won' in hand.get('result', ''):
                positions[pos]['wins'] += 1
        
        return dict(positions)
    
    def _identify_mistakes(self, hands: List[Dict]) -> List[str]:
        """Identify common mistakes."""
        mistakes = []
        
        # Check for overly passive play
        vpip = self._calculate_vpip(hands)
        if vpip < 15:
            mistakes.append("Playing too tight - missing profitable opportunities")
        elif vpip > 35:
            mistakes.append("Playing too loose - entering too many pots")
        
        # Check aggression
        aggression = self._calculate_aggression(hands)
        if aggression < 1.0:
            mistakes.append("Too passive - not betting/raising enough")
        
        # Check fold rate
        win_stats = self._calculate_win_rate(hands)
        fold_rate = (win_stats['folds'] / len(hands)) * 100
        if fold_rate > 70:
            mistakes.append("Folding too often - may be giving up too easily")
        
        return mistakes
    
    def _identify_strengths(self, hands: List[Dict]) -> List[str]:
        """Identify player strengths."""
        strengths = []
        
        vpip = self._calculate_vpip(hands)
        pfr = self._calculate_pfr(hands)
        aggression = self._calculate_aggression(hands)
        win_stats = self._calculate_win_rate(hands)
        
        if 20 <= vpip <= 30:
            strengths.append("Good hand selection - balanced range")
        
        if pfr >= 15:
            strengths.append("Aggressive pre-flop play - taking initiative")
        
        if aggression >= 2.0:
            strengths.append("Strong aggression - putting pressure on opponents")
        
        if win_stats['win_percentage'] >= 40:
            strengths.append("Solid win rate - making profitable decisions")
        
        return strengths
