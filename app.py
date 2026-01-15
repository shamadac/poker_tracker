"""Flask web application for poker hand analysis."""
import json
import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from hand_parser import HandParser
from ollama_analyzer import OllamaAnalyzer
from file_watcher import FileWatcher
from playstyle_analyzer import PlaystyleAnalyzer

app = Flask(__name__)
CORS(app)

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

parser = HandParser(config['player_username'])
analyzer = OllamaAnalyzer(config['ollama_url'], config['ollama_model'])
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
        'model': config['ollama_model'],
        'auto_detect_enabled': config.get('auto_detect_enabled', True)
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration."""
    data = request.json
    if 'username' in data:
        config['player_username'] = data['username']
    if 'model' in data:
        config['ollama_model'] = data['model']
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    return jsonify({'success': True})


@app.route('/api/scan', methods=['POST'])
def scan_hands():
    """Scan for new hand history files."""
    try:
        files = file_watcher.scan_for_files()
        hands = []
        
        for file_path in files:
            parsed = parser.parse_file(file_path)
            hands.extend(parsed)
        
        # Store hands in session for later use
        app.config['cached_hands'] = hands
        
        return jsonify({
            'success': True,
            'files_found': len(files),
            'hands_found': len(hands),
            'hands': [{'hand_id': h['hand_id'], 'cards': h['player_cards'], 
                      'result': h['result'], 'pot_size': h.get('pot_size', '0')} 
                      for h in hands[:20]]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze hands with comprehensive playstyle evaluation."""
    try:
        data = request.json
        analyze_all = data.get('analyze_all', False)
        include_individual = data.get('include_individual', False)
        limit = data.get('limit', 5)
        
        # Get cached hands or rescan
        all_hands = app.config.get('cached_hands', [])
        
        if not all_hands:
            files = file_watcher.scan_for_files()
            for file_path in files:
                parsed = parser.parse_file(file_path)
                all_hands.extend(parsed)
        
        if not all_hands:
            return jsonify({'success': False, 'error': 'No hands found'})
        
        # Generate comprehensive playstyle analysis from ALL hands
        playstyle_report = playstyle_analyzer.analyze_playstyle(all_hands)
        
        # Generate overall recommendations
        overall_analysis = analyzer.analyze_playstyle(playstyle_report, all_hands)
        
        # Only analyze individual hands if requested
        analyses = []
        if include_individual:
            hands_to_analyze = all_hands if analyze_all else all_hands[:limit]
            
            for hand in hands_to_analyze:
                analysis = analyzer.analyze_hand(hand)
                analyses.append({
                    'hand_id': hand['hand_id'],
                    'cards': hand['player_cards'],
                    'result': hand['result'],
                    'analysis': analysis,
                    'hand_details': {
                        'board': hand.get('board_cards', {}),
                        'pot_size': hand.get('pot_size', '0'),
                        'players': hand.get('players', []),
                        'betting_rounds': hand.get('betting_rounds', {}),
                        'showdown': hand.get('showdown', [])
                    }
                })
        
        return jsonify({
            'success': True,
            'total_hands': len(all_hands),
            'analyzed': len(analyses),
            'analyses': analyses,
            'playstyle_report': playstyle_report,
            'overall_recommendations': overall_analysis
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/progress', methods=['GET'])
def analyze_progress():
    """Get progress of ongoing analysis."""
    progress = app.config.get('analysis_progress', {
        'status': 'idle',
        'current': 0,
        'total': 0,
        'message': 'Ready'
    })
    return jsonify(progress)


@app.route('/api/status', methods=['GET'])
def status():
    """Check Ollama connection status."""
    try:
        import requests
        response = requests.get(f"{config['ollama_url']}/api/tags", timeout=2)
        return jsonify({'ollama_connected': response.status_code == 200})
    except:
        return jsonify({'ollama_connected': False})


@app.route('/api/hand/<hand_id>', methods=['GET'])
def get_hand_details(hand_id):
    """Get detailed information for a specific hand."""
    try:
        all_hands = app.config.get('cached_hands', [])
        
        for hand in all_hands:
            if hand['hand_id'] == hand_id:
                return jsonify({
                    'success': True,
                    'hand': hand
                })
        
        return jsonify({'success': False, 'error': 'Hand not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data."""
    try:
        all_hands = app.config.get('cached_hands', [])
        
        if not all_hands:
            files = file_watcher.scan_for_files()
            for file_path in files:
                parsed = parser.parse_file(file_path)
                all_hands.extend(parsed)
            app.config['cached_hands'] = all_hands
        
        if not all_hands:
            return jsonify({'success': False, 'error': 'No hands found'})
        
        # Separate play money and real money hands
        play_money_hands = [h for h in all_hands if h.get('is_play_money', False)]
        real_money_hands = [h for h in all_hands if not h.get('is_play_money', False)]
        
        # Calculate comprehensive statistics
        playstyle_report = playstyle_analyzer.analyze_playstyle(all_hands)
        
        # Calculate separate stats for play money and real money
        play_money_stats = playstyle_analyzer.analyze_playstyle(play_money_hands) if play_money_hands else None
        real_money_stats = playstyle_analyzer.analyze_playstyle(real_money_hands) if real_money_hands else None
        
        # Prepare hand list with key details
        hands_list = []
        for hand in all_hands:
            hands_list.append({
                'hand_id': hand['hand_id'],
                'date': hand.get('date', ''),
                'game_type': hand.get('game_type', ''),
                'stakes': hand.get('stakes', ''),
                'is_play_money': hand.get('is_play_money', False),
                'player_cards': hand['player_cards'],
                'result': hand['result'],
                'pot_size': hand.get('pot_size', '0'),
                'position': hand.get('player_position', 'Unknown'),
                'actions': len(hand.get('actions', [])),
                'won': 'won' in hand.get('result', '').lower()
            })
        
        return jsonify({
            'success': True,
            'stats': playstyle_report,
            'play_money_stats': play_money_stats,
            'real_money_stats': real_money_stats,
            'hands': hands_list,
            'total_hands': len(all_hands),
            'play_money_count': len(play_money_hands),
            'real_money_count': len(real_money_hands)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("🃏 Poker Analyzer Web UI")
    print("=" * 50)
    print(f"Player: {config['player_username']}")
    print(f"Model: {config['ollama_model']}")
    print("\n🌐 Starting server at http://localhost:5000")
    print("Open this URL in Chrome to use the app\n")
    app.run(debug=True, host='0.0.0.0', port=5001)
