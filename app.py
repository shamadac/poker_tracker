"""Flask web application for poker hand analysis."""
import json
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from hand_parser import HandParser
from ai_provider import AIProvider
from file_watcher import FileWatcher
from playstyle_analyzer import PlaystyleAnalyzer

app = Flask(__name__)
CORS(app)

# Load config
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()
parser = HandParser(config['player_username'])
ai_provider = AIProvider(config)
file_watcher = FileWatcher(config)
playstyle_analyzer = PlaystyleAnalyzer(config['player_username'])


@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Serve the statistics dashboard page."""
    return render_template('dashboard.html')


@app.route('/graphs')
def graphs():
    """Serve the graphs and charts page."""
    return render_template('graphs.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration."""
    return jsonify({
        'username': config['player_username'],
        'ai_provider': config.get('ai_provider', 'ollama'),
        'ollama_model': config.get('ollama_model', 'llama2'),
        'gemini_model': config.get('gemini_model', 'gemini-pro'),
        'has_gemini_key': bool(config.get('gemini_api_key', ''))
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    global config, ai_provider
    
    data = request.json
    
    if 'username' in data:
        config['player_username'] = data['username']
    if 'ai_provider' in data:
        config['ai_provider'] = data['ai_provider']
    if 'ollama_model' in data:
        config['ollama_model'] = data['ollama_model']
    if 'gemini_api_key' in data:
        config['gemini_api_key'] = data['gemini_api_key']
    if 'gemini_model' in data:
        config['gemini_model'] = data['gemini_model']
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Reinitialize AI provider
    ai_provider = AIProvider(config)
    
    return jsonify({'success': True})


@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Check AI provider status."""
    status = ai_provider.check_status()
    return jsonify(status)


@app.route('/api/ai/install-ollama', methods=['POST'])
def install_ollama():
    """Install Ollama."""
    success, message = ai_provider.install_ollama()
    return jsonify({'success': success, 'message': message})


@app.route('/api/ai/pull-model', methods=['POST'])
def pull_model():
    """Pull Ollama model."""
    data = request.json
    model_name = data.get('model', config.get('ollama_model'))
    success, message = ai_provider.pull_model(model_name)
    return jsonify({'success': success, 'message': message})


@app.route('/api/scan', methods=['POST'])
def scan_hands():
    """Scan for new hand history files."""
    try:
        files = file_watcher.scan_for_files()
        hands = []
        
        for file_path in files:
            parsed = parser.parse_file(file_path)
            hands.extend(parsed)
        
        return jsonify({
            'success': True,
            'files_found': len(files),
            'hands_found': len(hands),
            'hands': [{'hand_id': h['hand_id'], 'cards': h['player_cards'], 
                      'result': h['result']} for h in hands[:20]]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze hands."""
    try:
        data = request.json
        limit = data.get('limit', 5)
        
        files = file_watcher.scan_for_files()
        all_hands = []
        
        for file_path in files:
            parsed = parser.parse_file(file_path)
            all_hands.extend(parsed)
        
        if not all_hands:
            return jsonify({'success': False, 'error': 'No hands found'})
        
        # Analyze limited number of hands
        hands_to_analyze = all_hands[:limit]
        analyses = []
        
        for hand in hands_to_analyze:
            analysis = ai_provider.analyze_hand(hand)
            analyses.append({
                'hand_id': hand['hand_id'],
                'cards': hand['player_cards'],
                'result': hand['result'],
                'analysis': analysis
            })
        
        return jsonify({
            'success': True,
            'total_hands': len(all_hands),
            'analyzed': len(analyses),
            'analyses': analyses
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/summary', methods=['POST'])
def analyze_summary():
    """Analyze all hands and provide summary with playstyle analysis."""
    try:
        files = file_watcher.scan_for_files()
        all_hands = []
        
        for file_path in files:
            parsed = parser.parse_file(file_path)
            all_hands.extend(parsed)
        
        if not all_hands:
            return jsonify({'success': False, 'error': 'No hands found'})
        
        # Get playstyle statistics
        stats = playstyle_analyzer.analyze_playstyle(all_hands)
        
        # Generate AI summary based on stats with detailed beginner-friendly structure
        summary_prompt = f"""You are a friendly poker coach helping a BEGINNER player improve their game. Use simple language and explain concepts clearly.

PLAYER STATISTICS (from {stats.get('total_hands', 0)} hands):
- VPIP: {stats.get('vpip', 0)}% (how often they play hands)
- PFR: {stats.get('pfr', 0)}% (how often they raise before the flop)
- Aggression: {stats.get('aggression', 0)} (how aggressive vs passive)
- Win Rate: {stats.get('win_rate', {}).get('win_percentage', 0)}%
- Results: {stats.get('win_rate', {}).get('wins', 0)} wins, {stats.get('win_rate', {}).get('losses', 0)} losses, {stats.get('win_rate', {}).get('folds', 0)} folds

Common Mistakes Detected:
{chr(10).join('- ' + m for m in stats.get('common_mistakes', [])) if stats.get('common_mistakes') else '- None identified'}

Strengths Identified:
{chr(10).join('- ' + s for s in stats.get('strengths', [])) if stats.get('strengths') else '- Building skills'}

Write a BEGINNER-FRIENDLY analysis with these sections:

## 🎮 YOUR PLAYING STYLE
Describe their style in simple terms. Are they tight or loose? Aggressive or passive? What does this mean for a beginner?

## ✅ WHAT YOU'RE DOING WELL (Top 3-5 Strengths)
List their strengths. Use simple language and explain WHY each is good.

## ❌ MISTAKES TO FIX (Top 3-5 Problems)
List mistakes they're making. Explain WHAT the mistake is, WHY it's bad, and HOW it costs them money.

## 💪 HOW TO IMPROVE (Top 3-5 Action Items)
Give specific things to practice. Make each one actionable and explain the concept if needed.
For example, if mentioning "position", briefly explain what position means in poker.

## 📚 POKER CONCEPTS TO LEARN
Explain 1-2 important poker concepts this player needs to understand (like position, pot odds, hand selection, etc.). 
Keep explanations simple and practical.

## 🎯 QUICK TIPS FOR NEXT SESSION
Give 2-3 simple tips they can use immediately in their next game.

Remember: This player is a BEGINNER. Avoid jargon. When you must use poker terms, explain them simply."""

        summary_hand = {
            'hand_id': 'SUMMARY',
            'game_type': 'Overall Analysis',
            'stakes': '',
            'player_cards': '',
            'result': f'{stats.get("total_hands", 0)} hands analyzed',
            'actions': [],
            'raw_text': summary_prompt
        }
        
        ai_summary = ai_provider.analyze_hand(summary_hand)
        
        return jsonify({
            'success': True,
            'total_hands': len(all_hands),
            'stats': stats,
            'ai_summary': ai_summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("🃏 Poker Analyzer Web UI")
    print("=" * 50)
    print(f"Player: {config['player_username']}")
    print(f"AI Provider: {config.get('ai_provider', 'ollama')}")
    print("\n🌐 Starting server at http://localhost:5000")
    print("Open this URL in Chrome to use the app\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
