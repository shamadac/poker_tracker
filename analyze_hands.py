"""Main script to analyze poker hands."""
import json
import os
from datetime import datetime
from pathlib import Path
from hand_parser import HandParser
from ollama_analyzer import OllamaAnalyzer


def load_config():
    """Load configuration from config.json."""
    with open('config.json', 'r') as f:
        return json.load(f)


def ensure_directories(config):
    """Create necessary directories if they don't exist."""
    Path(config['hand_history_dir']).mkdir(exist_ok=True)
    Path(config['reports_dir']).mkdir(exist_ok=True)


def main():
    """Main analysis workflow."""
    print("🃏 Poker Hand Analyzer")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    ensure_directories(config)
    
    # Initialize components
    parser = HandParser(config['player_username'])
    analyzer = OllamaAnalyzer(config['ollama_url'], config['ollama_model'])
    
    # Find hand history files
    hand_history_dir = Path(config['hand_history_dir'])
    history_files = list(hand_history_dir.glob('*.txt'))
    
    if not history_files:
        print(f"\n❌ No hand history files found in '{config['hand_history_dir']}/'")
        print("\nTo get started:")
        print("1. Export hand histories from PokerStars")
        print(f"2. Place .txt files in the '{config['hand_history_dir']}/' folder")
        print("3. Run this script again")
        return
    
    print(f"\n📁 Found {len(history_files)} hand history file(s)")
    
    # Parse all hands
    all_hands = []
    for file in history_files:
        print(f"   Parsing: {file.name}")
        hands = parser.parse_file(str(file))
        all_hands.extend(hands)
    
    print(f"\n✅ Parsed {len(all_hands)} hands for player '{config['player_username']}'")
    
    if not all_hands:
        print("\n⚠️  No hands found for the configured player")
        return
    
    # Analyze hands
    print(f"\n🤖 Analyzing hands with Ollama ({config['ollama_model']})...")
    print("   This may take a few minutes...\n")
    
    analyses = []
    for i, hand in enumerate(all_hands[:5], 1):  # Analyze first 5 hands
        print(f"   [{i}/5] Analyzing hand #{hand['hand_id']}...")
        analysis = analyzer.analyze_hand(hand)
        analyses.append({
            'hand_id': hand['hand_id'],
            'cards': hand['player_cards'],
            'result': hand['result'],
            'analysis': analysis
        })
    
    # Generate report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = Path(config['reports_dir']) / f'analysis_{timestamp}.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Poker Analysis Report for {config['player_username']}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        for analysis in analyses:
            f.write(f"Hand #{analysis['hand_id']}\n")
            f.write(f"Cards: {analysis['cards']}\n")
            f.write(f"Result: {analysis['result']}\n")
            f.write("-" * 70 + "\n")
            f.write(f"{analysis['analysis']}\n")
            f.write("\n" + "=" * 70 + "\n\n")
    
    print(f"\n✅ Analysis complete!")
    print(f"📄 Report saved to: {report_file}")
    print(f"\n💡 Analyzed {len(analyses)} hands. Review the report for insights!")


if __name__ == '__main__':
    main()
