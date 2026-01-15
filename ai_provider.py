"""Unified AI provider interface supporting Ollama and Gemini."""
import os
import subprocess
import platform
import requests
from typing import Dict, Tuple
import google.generativeai as genai


class AIProvider:
    """Manage AI providers (Ollama or Gemini)."""
    
    def __init__(self, config):
        self.config = config
        self.provider = config.get('ai_provider', 'ollama')
        
        if self.provider == 'gemini':
            api_key = config.get('gemini_api_key', '')
            if api_key:
                genai.configure(api_key=api_key)
    
    def check_status(self) -> Dict:
        """Check if the selected AI provider is ready."""
        if self.provider == 'ollama':
            return self._check_ollama_status()
        elif self.provider == 'gemini':
            return self._check_gemini_status()
        return {'ready': False, 'error': 'Unknown provider'}
    
    def _check_ollama_status(self) -> Dict:
        """Check Ollama installation and model availability."""
        # Check if Ollama is installed
        if not self._is_ollama_installed():
            return {
                'ready': False,
                'installed': False,
                'model_available': False,
                'message': 'Ollama not installed',
                'can_auto_install': True
            }
        
        # Check if Ollama is running
        try:
            response = requests.get(f"{self.config['ollama_url']}/api/tags", timeout=2)
            if response.status_code != 200:
                return {
                    'ready': False,
                    'installed': True,
                    'running': False,
                    'message': 'Ollama not running'
                }
            
            # Check if model is available
            models = response.json().get('models', [])
            model_name = self.config['ollama_model']
            model_available = any(model_name in m.get('name', '') for m in models)
            
            if not model_available:
                return {
                    'ready': False,
                    'installed': True,
                    'running': True,
                    'model_available': False,
                    'message': f'Model {model_name} not installed',
                    'can_auto_install': True
                }
            
            return {
                'ready': True,
                'installed': True,
                'running': True,
                'model_available': True,
                'message': 'Ollama ready'
            }
        
        except requests.exceptions.RequestException:
            return {
                'ready': False,
                'installed': True,
                'running': False,
                'message': 'Ollama not running'
            }
    
    def _check_gemini_status(self) -> Dict:
        """Check Gemini API key validity."""
        api_key = self.config.get('gemini_api_key', '')
        
        if not api_key:
            return {
                'ready': False,
                'message': 'Gemini API key not configured'
            }
        
        try:
            # Test API key with a simple request
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.config.get('gemini_model', 'gemini-pro'))
            # Just check if we can access the model
            return {
                'ready': True,
                'message': 'Gemini API ready'
            }
        except Exception as e:
            return {
                'ready': False,
                'message': f'Gemini API error: {str(e)}'
            }
    
    def _is_ollama_installed(self) -> bool:
        """Check if Ollama is installed."""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def install_ollama(self) -> Tuple[bool, str]:
        """Attempt to install Ollama (platform-specific)."""
        system = platform.system()
        
        if system == 'Darwin':  # MacOS
            return self._install_ollama_mac()
        elif system == 'Linux':
            return self._install_ollama_linux()
        elif system == 'Windows':
            return self._install_ollama_windows()
        
        return False, f'Unsupported platform: {system}'
    
    def _install_ollama_mac(self) -> Tuple[bool, str]:
        """Install Ollama on MacOS."""
        try:
            # Check if Homebrew is available
            subprocess.run(['brew', '--version'], capture_output=True, check=True)
            
            # Install via Homebrew
            result = subprocess.run(['brew', 'install', 'ollama'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=300)
            
            if result.returncode == 0:
                return True, 'Ollama installed successfully'
            return False, f'Installation failed: {result.stderr}'
        
        except subprocess.CalledProcessError:
            return False, 'Homebrew not found. Please install from https://ollama.ai/download'
        except Exception as e:
            return False, f'Installation error: {str(e)}'
    
    def _install_ollama_linux(self) -> Tuple[bool, str]:
        """Install Ollama on Linux."""
        try:
            # Use official install script
            result = subprocess.run(
                ['curl', '-fsSL', 'https://ollama.ai/install.sh'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                subprocess.run(['sh', '-c', result.stdout], timeout=300)
                return True, 'Ollama installed successfully'
            
            return False, 'Installation failed'
        except Exception as e:
            return False, f'Installation error: {str(e)}'
    
    def _install_ollama_windows(self) -> Tuple[bool, str]:
        """Windows requires manual installation."""
        return False, 'Please download and install from https://ollama.ai/download'
    
    def pull_model(self, model_name: str = None) -> Tuple[bool, str]:
        """Pull/download an Ollama model."""
        if not model_name:
            model_name = self.config['ollama_model']
        
        try:
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for large models
            )
            
            if result.returncode == 0:
                return True, f'Model {model_name} installed successfully'
            return False, f'Failed to pull model: {result.stderr}'
        
        except subprocess.TimeoutExpired:
            return False, 'Model download timed out'
        except Exception as e:
            return False, f'Error pulling model: {str(e)}'
    
    def analyze_hand(self, hand_data: Dict) -> str:
        """Analyze a hand using the selected provider."""
        if self.provider == 'ollama':
            return self._analyze_with_ollama(hand_data)
        elif self.provider == 'gemini':
            return self._analyze_with_gemini(hand_data)
        return 'Error: Unknown AI provider'
    
    def _analyze_with_ollama(self, hand_data: Dict) -> str:
        """Analyze using Ollama."""
        prompt = self._build_prompt(hand_data)
        
        try:
            response = requests.post(
                f"{self.config['ollama_url']}/api/generate",
                json={
                    'model': self.config['ollama_model'],
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
    
    def _analyze_with_gemini(self, hand_data: Dict) -> str:
        """Analyze using Gemini."""
        prompt = self._build_prompt(hand_data)
        
        try:
            model = genai.GenerativeModel(self.config.get('gemini_model', 'gemini-pro'))
            response = model.generate_content(prompt)
            
            # Check if response was blocked
            if not response.candidates:
                return "⚠️ Analysis unavailable: Response was blocked by safety filters. This is rare - try analyzing another hand."
            
            candidate = response.candidates[0]
            if candidate.finish_reason != 1:  # 1 = STOP (normal completion)
                return f"⚠️ Analysis incomplete: Response ended early (reason: {candidate.finish_reason}). Try again or use a different model."
            
            if not response.text:
                return "⚠️ No analysis generated. Please try again."
            
            return response.text
        
        except Exception as e:
            return f'Error with Gemini API: {str(e)}'
    
    def _build_prompt(self, hand_data: Dict) -> str:
        """Build analysis prompt from hand data."""
        # Check if this is a summary analysis
        if hand_data.get('hand_id') == 'SUMMARY':
            return hand_data.get('raw_text', '')
        
        # Individual hand analysis with beginner-friendly structure
        prompt = f"""You are a friendly poker coach helping a BEGINNER player improve. Use simple language and explain concepts clearly.

HAND DETAILS:
- Hand ID: {hand_data['hand_id']}
- Game: {hand_data['game_type']}
- Stakes: {hand_data['stakes']}
- Your Cards: {hand_data['player_cards']}
- Result: {hand_data['result']}

WHAT HAPPENED:
{chr(10).join(hand_data['actions']) if hand_data['actions'] else 'No actions recorded'}

FULL HAND:
{hand_data['raw_text'][:1000]}

Provide a BEGINNER-FRIENDLY analysis with these sections:

## 🎯 QUICK SUMMARY
One sentence: What was the key decision in this hand?

## ✅ WHAT YOU DID WELL
List 2-3 good decisions. Explain WHY each was smart.

## ❌ MISTAKES TO AVOID
List any mistakes. Explain WHAT went wrong, WHY it's bad, and HOW to fix it.

## 💡 KEY LESSON
What's the ONE thing to remember from this hand? Keep it simple and actionable.

## 📚 CONCEPT TO LEARN (if relevant)
If this hand teaches an important poker concept (like position, pot odds, hand selection), explain it simply.

Remember: Use simple language. Avoid jargon. When you must use poker terms, explain them."""
        
        return prompt
