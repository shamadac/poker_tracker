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
        prompt = f"""You are an expert poker coach providing a comprehensive evaluation of a player's overall game.

PLAYER STATISTICS (from {stats.get('total_hands', 0)} hands):
- VPIP (Voluntarily Put $ In Pot): {stats.get('vpip', 0)}%
- PFR (Pre-Flop Raise): {stats.get('pfr', 0)}%
- Aggression Factor: {stats.get('aggression', 0)}
- Win Rate: {stats.get('win_rate', {}).get('win_percentage', 0)}%
- Wins: {stats.get('win_rate', {}).get('wins', 0)}
- Losses: {stats.get('win_rate', {}).get('losses', 0)}
- Folds: {stats.get('win_rate', {}).get('folds', 0)}

IDENTIFIED STRENGTHS:
{chr(10).join('- ' + s for s in stats.get('strengths', [])) if stats.get('strengths') else '- None identified yet'}

COMMON MISTAKES:
{chr(10).join('- ' + m for m in stats.get('common_mistakes', [])) if stats.get('common_mistakes') else '- None identified yet'}

Provide a comprehensive evaluation covering:

1. OVERALL ASSESSMENT
   - What type of player are they? (tight/loose, aggressive/passive)
   - How does their playstyle compare to winning poker?

2. KEY STRENGTHS
   - What are they doing well?
   - Which aspects of their game are solid?

3. CRITICAL WEAKNESSES
   - What are the biggest leaks in their game?
   - What mistakes are costing them money?

4. SPECIFIC IMPROVEMENT PLAN
   - Top 3 things to work on immediately
   - Concrete actions they can take
   - Expected impact of these changes

5. LONG-TERM DEVELOPMENT
   - Skills to develop over time
   - Resources or concepts to study
   - Mindset adjustments needed

Be direct, specific, and actionable. Focus on what will make the biggest difference to their win rate."""
        
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
