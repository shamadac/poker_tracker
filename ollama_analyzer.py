"""Analyze poker hands using Ollama."""
import json
import requests
from typing import Dict


class OllamaAnalyzer:
    """Use Ollama to analyze poker hands."""
    
    def __init__(self, ollama_url: str, model: str):
        self.ollama_url = ollama_url
        self.model = model
    
    def analyze_hand(self, hand_data: Dict) -> str:
        """Analyze a single hand and return strategic advice."""
        prompt = self._build_prompt(hand_data)
        
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No analysis available')
            else:
                return f'Error: Ollama returned status {response.status_code}'
        
        except requests.exceptions.RequestException as e:
            return f'Error connecting to Ollama: {str(e)}'
    
    def analyze_playstyle(self, stats: Dict, hands: list) -> str:
        """Generate comprehensive playstyle analysis and recommendations."""
        prompt = f"""You are a friendly poker coach helping a BEGINNER player improve their game. Use simple language and explain concepts clearly.

PLAYER STATISTICS (from {stats.get('total_hands', 0)} hands):
- VPIP: {stats.get('vpip', 0)}% (how often they play hands)
- PFR: {stats.get('pfr', 0)}% (how often they raise before the flop)
- Aggression: {stats.get('aggression', 0)} (how aggressive vs passive)
- Win Rate: {stats.get('win_rate', {}).get('win_percentage', 0)}%
- Results: {stats.get('win_rate', {}).get('wins', 0)} wins, {stats.get('win_rate', {}).get('losses', 0)} losses, {stats.get('win_rate', {}).get('folds', 0)} folds

Write a BEGINNER-FRIENDLY analysis with these sections:

## YOUR PLAYING STYLE
Describe their style in simple terms. Are they tight or loose? Aggressive or passive? What does this mean for a beginner?

## WHAT YOU'RE DOING WELL (Top 5 Strengths)
List 5 things they're doing right. Use simple language and explain WHY each is good.

## MISTAKES TO FIX (Top 5 Problems)
List 5 mistakes they're making. Explain WHAT the mistake is, WHY it's bad, and HOW it costs them money.

## HOW TO IMPROVE (Top 5 Action Items)
Give 5 specific things to practice. Make each one actionable and explain the concept if needed.
For example, if mentioning "position", briefly explain what position means in poker.

## POKER CONCEPTS TO LEARN
Explain 2-3 important poker concepts this player needs to understand (like position, pot odds, hand selection, etc.). 
Keep explanations simple and practical.

## QUICK TIPS FOR NEXT SESSION
Give 2-3 simple tips they can use immediately in their next game.

Remember: This player is a BEGINNER. Avoid jargon. When you must use poker terms, explain them simply."""
        
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No analysis available')
            else:
                return f'Error: Ollama returned status {response.status_code}'
        
        except requests.exceptions.RequestException as e:
            return f'Error connecting to Ollama: {str(e)}'
    
    def _build_prompt(self, hand_data: Dict) -> str:
        """Build analysis prompt from hand data."""
        prompt = f"""You are an expert poker coach analyzing a hand. Provide strategic advice.

Hand ID: {hand_data['hand_id']}
Game: {hand_data['game_type']}
Stakes: {hand_data['stakes']}
Player Cards: {hand_data['player_cards']}
Result: {hand_data['result']}

Player Actions:
{chr(10).join(hand_data['actions']) if hand_data['actions'] else 'No actions recorded'}

Full Hand History:
{hand_data['raw_text'][:1000]}

Analyze this hand and provide:
1. What the player did well
2. Mistakes or missed opportunities
3. Specific advice for improvement
4. Key takeaway

Keep your analysis concise and actionable."""
        
        return prompt
