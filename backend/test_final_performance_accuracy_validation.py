"""
Final performance and accuracy validation tests.
Validates parsing accuracy requirements and performance benchmarks.
Requirements: 5.1, 5.6
"""
import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any
from pathlib import Path
import tempfile
import os

from app.services.hand_parser import HandParserService
from app.services.pokerstars_parser import PokerStarsParser
from app.services.ggpoker_parser import GGPokerParser
from app.services.hand_validator import HandValidator
from app.models.hand import PokerHand


class TestParsingAccuracyValidation:
    """Test parsing accuracy requirements (99%+ accuracy)."""
    
    @pytest.fixture
    def sample_pokerstars_hands(self):
        """Sample PokerStars hand histories for testing."""
        return [
            # Valid tournament hand
            """PokerStars Hand #123456789: Tournament #987654321, $10+$1 USD Hold'em No Limit - Level I (10/20) - 2024/01/15 20:00:00 ET
Table '987654321 1' 9-max Seat #1 is the button
Seat 1: Player1 (1500 in chips)
Seat 2: Player2 (1500 in chips)
Seat 3: Player3 (1500 in chips)
Player2: posts small blind 10
Player3: posts big blind 20
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises 40 to 60
Player2: folds
Player3: calls 40
*** FLOP *** [Ac 7h 2d]
Player3: checks
Player1: bets 80
Player3: calls 80
*** TURN *** [Ac 7h 2d] [Kd]
Player3: checks
Player1: bets 160
Player3: folds
Uncalled bet (160) returned to Player1
Player1 collected 300 from pot
*** SUMMARY ***
Total pot 300 | Rake 0
Board [Ac 7h 2d Kd]
Seat 1: Player1 (button) collected (300)
Seat 2: Player2 (small blind) folded before Flop
Seat 3: Player3 (big blind) folded on the Turn""",
            
            # Valid cash game hand
            """PokerStars Hand #234567890: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:05:00 ET
Table 'TestTable' 6-max Seat #3 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
Seat 3: Player3 ($120.25 in chips)
Player1: posts small blind $0.50
Player2: posts big blind $1.00
*** HOLE CARDS ***
Dealt to Player1 [Qd Qh]
Player3: raises $3.00 to $4.00
Player1: calls $3.50
Player2: folds
*** FLOP *** [9s 4c 2h]
Player1: checks
Player3: bets $6.00
Player1: raises $18.00 to $24.00
Player3: folds
Uncalled bet ($18.00) returned to Player1
Player1 collected $21.00 from pot
*** SUMMARY ***
Total pot $21.00 | Rake $1.00
Board [9s 4c 2h]
Seat 1: Player1 (small blind) collected ($21.00)
Seat 2: Player2 (big blind) folded before Flop
Seat 3: Player3 (button) folded on the Flop""",
            
            # Hand with all-in
            """PokerStars Hand #345678901: Hold'em No Limit ($1/$2 USD) - 2024/01/15 20:10:00 ET
Table 'HighStakes' 9-max Seat #5 is the button
Seat 1: Player1 ($200.00 in chips)
Seat 5: Player5 ($180.50 in chips)
Seat 9: Player9 ($220.75 in chips)
Player9: posts small blind $1
Player1: posts big blind $2
*** HOLE CARDS ***
Dealt to Player1 [Ad Ah]
Player5: raises $6 to $8
Player9: folds
Player1: raises $20 to $28
Player5: calls $20
*** FLOP *** [8h 3c 2s]
Player1: bets $35
Player5: raises $117.50 to $152.50 and is all-in
Player1: calls $117.50
*** TURN *** [8h 3c 2s] [Kd]
*** RIVER *** [8h 3c 2s Kd] [7h]
*** SHOW DOWN ***
Player1: shows [Ad Ah] (a pair of Aces)
Player5: shows [8s 8c] (three of a kind, Eights)
Player5 collected $359.00 from pot
*** SUMMARY ***
Total pot $362.00 | Rake $3.00
Board [8h 3c 2s Kd 7h]
Seat 1: Player1 (big blind) showed [Ad Ah] and lost with a pair of Aces
Seat 5: Player5 (button) showed [8s 8c] and won ($359.00) with three of a kind, Eights
Seat 9: Player9 (small blind) folded before Flop""",
            
            # Corrupted hand (should fail parsing)
            """PokerStars Hand #INVALID: This is not a valid hand
Invalid data here
*** HOLE CARDS ***
Missing required information""",
            
            # Incomplete hand (should fail validation)
            """PokerStars Hand #456789012: Hold'em No Limit ($0.25/$0.50 USD) - 2024/01/15 20:15:00 ET
Table 'Incomplete' 6-max Seat #1 is the button
Seat 1: Player1 ($50.00 in chips)
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises $1.50 to $2.00
*** SUMMARY ***
Total pot $2.00 | Rake $0.00"""
        ]
    
    @pytest.fixture
    def sample_ggpoker_hands(self):
        """Sample GGPoker hand histories for testing."""
        return [
            # Valid GGPoker hand
            """GG Poker Hand #123456789: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 ET
Table 'GGTable' 6-max Seat #2 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
Seat 3: Player3 ($120.25 in chips)
Player3: posts small blind $0.50
Player1: posts big blind $1.00
*** HOLE CARDS ***
Dealt to Player1 [Js Jh]
Player2: raises $3.00 to $4.00
Player3: folds
Player1: calls $3.00
*** FLOP *** [Tc 5d 2h]
Player1: checks
Player2: bets $6.00
Player1: calls $6.00
*** TURN *** [Tc 5d 2h] [Jd]
Player1: checks
Player2: bets $12.00
Player1: raises $24.00 to $36.00
Player2: folds
Uncalled bet ($24.00) returned to Player1
Player1 collected $31.50 from pot
*** SUMMARY ***
Total pot $32.50 | Rake $1.00
Board [Tc 5d 2h Jd]
Seat 1: Player1 (big blind) collected ($31.50)
Seat 2: Player2 (button) folded on the Turn
Seat 3: Player3 (small blind) folded before Flop""",
            
            # Invalid GGPoker hand
            """GG Poker Hand #INVALID: This is corrupted
Missing data everywhere"""
        ]
    
    async def test_pokerstars_parsing_accuracy(self, sample_pokerstars_hands):
        """Test PokerStars parsing accuracy meets 99%+ requirement."""
        parser = PokerStarsParser()
        
        total_hands = len(sample_pokerstars_hands)
        successfully_parsed = 0
        validation_errors = []
        
        for i, hand_text in enumerate(sample_pokerstars_hands):
            try:
                # Parse the hand using the correct method
                if parser.can_parse(hand_text):
                    parsed_hands = parser.parse_hands(hand_text)
                    
                    if parsed_hands:
                        # Validate the first parsed hand
                        hand = parsed_hands[0]
                        is_valid = parser.validate_hand(hand)
                        
                        if is_valid:
                            successfully_parsed += 1
                        else:
                            validation_errors.append(f"Hand {i}: Validation failed")
                            
            except Exception as e:
                # Expected for corrupted hands
                if "INVALID" not in hand_text and "Incomplete" not in hand_text:
                    validation_errors.append(f"Hand {i}: Unexpected parsing error: {e}")
        
        # Calculate accuracy (excluding intentionally corrupted hands)
        valid_hands = [h for h in sample_pokerstars_hands if "INVALID" not in h and "Incomplete" not in h]
        expected_successful = len(valid_hands)
        accuracy = (successfully_parsed / expected_successful) * 100 if expected_successful > 0 else 0
        
        print(f"PokerStars Parsing Accuracy: {accuracy:.2f}%")
        print(f"Successfully parsed: {successfully_parsed}/{expected_successful}")
        
        if validation_errors:
            print("Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
        
        # Requirement: 99%+ parsing accuracy
        assert accuracy >= 99.0, f"Parsing accuracy {accuracy:.2f}% is below required 99%"
    
    async def test_ggpoker_parsing_accuracy(self, sample_ggpoker_hands):
        """Test GGPoker parsing accuracy meets 99%+ requirement."""
        parser = GGPokerParser()
        
        total_hands = len(sample_ggpoker_hands)
        successfully_parsed = 0
        validation_errors = []
        
        for i, hand_text in enumerate(sample_ggpoker_hands):
            try:
                # Parse the hand using the correct method
                if parser.can_parse(hand_text):
                    parsed_hands = parser.parse_hands(hand_text)
                    
                    if parsed_hands:
                        # Validate the first parsed hand
                        hand = parsed_hands[0]
                        is_valid = parser.validate_hand(hand)
                        
                        if is_valid:
                            successfully_parsed += 1
                        else:
                            validation_errors.append(f"Hand {i}: Validation failed")
                            
            except Exception as e:
                # Expected for corrupted hands
                if "INVALID" not in hand_text:
                    validation_errors.append(f"Hand {i}: Unexpected parsing error: {e}")
        
        # Calculate accuracy (excluding intentionally corrupted hands)
        valid_hands = [h for h in sample_ggpoker_hands if "INVALID" not in h]
        expected_successful = len(valid_hands)
        accuracy = (successfully_parsed / expected_successful) * 100 if expected_successful > 0 else 0
        
        print(f"GGPoker Parsing Accuracy: {accuracy:.2f}%")
        print(f"Successfully parsed: {successfully_parsed}/{expected_successful}")
        
        if validation_errors:
            print("Validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
        
        # Requirement: 99%+ parsing accuracy
        assert accuracy >= 99.0, f"Parsing accuracy {accuracy:.2f}% is below required 99%"
    
    async def test_multi_platform_parsing_accuracy(self, sample_pokerstars_hands, sample_ggpoker_hands):
        """Test overall multi-platform parsing accuracy."""
        parser_service = HandParserService()
        
        all_hands = sample_pokerstars_hands + sample_ggpoker_hands
        total_hands = len(all_hands)
        successfully_parsed = 0
        
        for hand_text in all_hands:
            try:
                # Auto-detect platform and parse
                platform = parser_service.detect_platform(hand_text)
                valid_hands, error_details = parser_service.parse_content(hand_text)
                
                if valid_hands:
                    successfully_parsed += 1
                    
            except Exception as e:
                # Expected for corrupted hands
                if "INVALID" not in hand_text and "Incomplete" not in hand_text:
                    print(f"Unexpected error: {e}")
        
        # Calculate overall accuracy (excluding corrupted hands)
        valid_hands = [h for h in all_hands if "INVALID" not in h and "Incomplete" not in h]
        expected_successful = len(valid_hands)
        overall_accuracy = (successfully_parsed / expected_successful) * 100 if expected_successful > 0 else 0
        
        print(f"Overall Multi-Platform Parsing Accuracy: {overall_accuracy:.2f}%")
        print(f"Successfully parsed: {successfully_parsed}/{expected_successful}")
        
        # Requirement: 99%+ parsing accuracy across all platforms
        assert overall_accuracy >= 99.0, f"Overall parsing accuracy {overall_accuracy:.2f}% is below required 99%"


class TestPerformanceBenchmarks:
    """Test performance requirements compliance."""
    
    @pytest.fixture
    def large_hand_history_file(self):
        """Create a large hand history file for performance testing."""
        hand_template = """PokerStars Hand #{hand_id}: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:{minute:02d}:00 ET
Table 'PerfTest' 6-max Seat #1 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
Player2: posts small blind $0.50
Player1: posts big blind $1.00
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises $2.50 to $3.50
Player2: calls $3.00
*** FLOP *** [Ac 7h 2d]
Player2: checks
Player1: bets $5.00
Player2: calls $5.00
*** TURN *** [Ac 7h 2d] [Kd]
Player2: checks
Player1: bets $10.00
Player2: folds
Uncalled bet ($10.00) returned to Player1
Player1 collected $16.50 from pot
*** SUMMARY ***
Total pot $17.00 | Rake $0.50
Board [Ac 7h 2d Kd]
Seat 1: Player1 (big blind) collected ($16.50)
Seat 2: Player2 (small blind) folded on the Turn

"""
        
        # Generate 1000 hands
        hands = []
        for i in range(1000):
            hand_id = 123456789 + i
            minute = i % 60
            hands.append(hand_template.format(hand_id=hand_id, minute=minute))
        
        return "\n".join(hands)
    
    async def test_parsing_performance_1000_hands(self, large_hand_history_file):
        """Test parsing performance: 1000 hands within 30 seconds."""
        parser = PokerStarsParser()
        
        # Split into individual hands
        hands = [h.strip() for h in large_hand_history_file.split("\n\n") if h.strip()]
        
        print(f"Testing parsing performance with {len(hands)} hands")
        
        start_time = time.time()
        successfully_parsed = 0
        
        # Parse all hands
        for hand_text in hands:
            try:
                if parser.can_parse(hand_text):
                    parsed_hands = parser.parse_hands(hand_text)
                    if parsed_hands:
                        successfully_parsed += 1
            except Exception as e:
                print(f"Parsing error: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Parsed {successfully_parsed} hands in {total_time:.2f} seconds")
        print(f"Average time per hand: {(total_time / len(hands) * 1000):.2f}ms")
        
        # Requirement: Process 1000 hands within 30 seconds
        assert total_time <= 30.0, f"Parsing took {total_time:.2f}s, exceeds 30s requirement"
        
        # Ensure we parsed most hands successfully
        success_rate = (successfully_parsed / len(hands)) * 100
        assert success_rate >= 95.0, f"Success rate {success_rate:.2f}% is too low"
    
    async def test_concurrent_parsing_performance(self, large_hand_history_file):
        """Test concurrent parsing performance."""
        parser = PokerStarsParser()
        
        # Split into individual hands
        hands = [h.strip() for h in large_hand_history_file.split("\n\n") if h.strip()][:100]  # Use 100 hands for concurrency test
        
        print(f"Testing concurrent parsing with {len(hands)} hands")
        
        async def parse_hand(hand_text):
            try:
                if parser.can_parse(hand_text):
                    return parser.parse_hands(hand_text)
                return None
            except Exception:
                return None
        
        start_time = time.time()
        
        # Parse hands concurrently
        tasks = [parse_hand(hand_text) for hand_text in hands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successfully_parsed = sum(1 for result in results if result is not None and not isinstance(result, Exception) and result)
        
        print(f"Concurrently parsed {successfully_parsed} hands in {total_time:.2f} seconds")
        print(f"Average time per hand: {(total_time / len(hands) * 1000):.2f}ms")
        
        # Concurrent parsing should be faster than sequential
        # Allow up to 10 seconds for 100 hands concurrently
        assert total_time <= 10.0, f"Concurrent parsing took {total_time:.2f}s, too slow"
        
        success_rate = (successfully_parsed / len(hands)) * 100
        assert success_rate >= 95.0, f"Concurrent success rate {success_rate:.2f}% is too low"
    
    async def test_memory_usage_during_parsing(self, large_hand_history_file):
        """Test memory usage remains reasonable during parsing."""
        import psutil
        import os
        
        parser = PokerStarsParser()
        process = psutil.Process(os.getpid())
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        hands = [h.strip() for h in large_hand_history_file.split("\n\n") if h.strip()]
        
        print(f"Initial memory usage: {initial_memory:.2f} MB")
        
        # Parse hands and track memory
        memory_readings = [initial_memory]
        
        for i, hand_text in enumerate(hands):
            try:
                if parser.can_parse(hand_text):
                    parser.parse_hands(hand_text)
                
                # Take memory reading every 100 hands
                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_readings.append(current_memory)
                    
            except Exception:
                pass
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_readings.append(final_memory)
        
        max_memory = max(memory_readings)
        memory_increase = max_memory - initial_memory
        
        print(f"Final memory usage: {final_memory:.2f} MB")
        print(f"Maximum memory usage: {max_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory usage should not increase excessively (allow up to 100MB increase)
        assert memory_increase <= 100.0, f"Memory increased by {memory_increase:.2f}MB, too much"
    
    async def test_file_processing_performance(self):
        """Test file processing performance with temporary files."""
        parser_service = HandParserService()
        
        # Create a temporary file with multiple hands
        hand_content = """PokerStars Hand #123456789: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 ET
Table 'TestTable' 6-max Seat #1 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
Player2: posts small blind $0.50
Player1: posts big blind $1.00
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises $2.50 to $3.50
Player2: calls $3.00
*** FLOP *** [Ac 7h 2d]
Player2: checks
Player1: bets $5.00
Player2: calls $5.00
*** TURN *** [Ac 7h 2d] [Kd]
Player2: checks
Player1: bets $10.00
Player2: folds
Uncalled bet ($10.00) returned to Player1
Player1 collected $16.50 from pot
*** SUMMARY ***
Total pot $17.00 | Rake $0.50
Board [Ac 7h 2d Kd]
Seat 1: Player1 (big blind) collected ($16.50)
Seat 2: Player2 (small blind) folded on the Turn

"""
        
        # Repeat the hand 500 times to create a substantial file
        file_content = (hand_content * 500)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(file_content)
            temp_file_path = f.name
        
        try:
            file_size = os.path.getsize(temp_file_path) / 1024 / 1024  # MB
            print(f"Test file size: {file_size:.2f} MB")
            
            start_time = time.time()
            
            # Process the file
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            hands, error_details = parser_service.parse_content(content)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"Processed {len(hands)} hands from {file_size:.2f}MB file in {processing_time:.2f} seconds")
            print(f"Processing rate: {file_size / processing_time:.2f} MB/s")
            
            # Performance requirement: reasonable processing speed
            # Should process at least 1MB per 10 seconds
            max_allowed_time = file_size * 10  # 10 seconds per MB
            assert processing_time <= max_allowed_time, f"File processing too slow: {processing_time:.2f}s for {file_size:.2f}MB"
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)


class TestAccuracyBenchmarks:
    """Test specific accuracy benchmarks for different hand types."""
    
    async def test_tournament_hand_accuracy(self):
        """Test accuracy for tournament hands specifically."""
        parser = PokerStarsParser()
        
        tournament_hands = [
            """PokerStars Hand #123456789: Tournament #987654321, $10+$1 USD Hold'em No Limit - Level I (10/20) - 2024/01/15 20:00:00 ET
Table '987654321 1' 9-max Seat #1 is the button
Seat 1: Player1 (1500 in chips)
Seat 2: Player2 (1500 in chips)
Player2: posts small blind 10
Player1: posts big blind 20
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises 40 to 60
Player2: calls 40
*** FLOP *** [Ac 7h 2d]
Player2: checks
Player1: bets 80
Player2: folds
Uncalled bet (80) returned to Player1
Player1 collected 140 from pot
*** SUMMARY ***
Total pot 140 | Rake 0
Board [Ac 7h 2d]
Seat 1: Player1 (big blind) collected (140)
Seat 2: Player2 (small blind) folded on the Flop""",
            
            """PokerStars Hand #234567890: Tournament #987654321, $10+$1 USD Hold'em No Limit - Level II (15/30) - 2024/01/15 20:05:00 ET
Table '987654321 1' 9-max Seat #2 is the button
Seat 1: Player1 (1580 in chips)
Seat 2: Player2 (1420 in chips)
Player1: posts small blind 15
Player2: posts big blind 30
*** HOLE CARDS ***
Dealt to Player1 [Qd Qh]
Player1: raises 60 to 90
Player2: calls 60
*** FLOP *** [9s 4c 2h]
Player2: checks
Player1: bets 120
Player2: raises 240 to 360
Player1: raises 1130 to 1490 and is all-in
Player2: calls 970 and is all-in
Uncalled bet (160) returned to Player1
*** TURN *** [9s 4c 2h] [Kd]
*** RIVER *** [9s 4c 2h Kd] [7h]
*** SHOW DOWN ***
Player1: shows [Qd Qh] (a pair of Queens)
Player2: shows [9h 9c] (three of a kind, Nines)
Player2 collected 2840 from pot
*** SUMMARY ***
Total pot 2840 | Rake 0
Board [9s 4c 2h Kd 7h]
Seat 1: Player1 (small blind) showed [Qd Qh] and lost with a pair of Queens
Seat 2: Player2 (big blind) showed [9h 9c] and won (2840) with three of a kind, Nines"""
        ]
        
        successfully_parsed = 0
        
        for hand_text in tournament_hands:
            try:
                if parser.can_parse(hand_text):
                    parsed_hands = parser.parse_hands(hand_text)
                    
                    if parsed_hands:
                        hand = parsed_hands[0]
                        is_valid = parser.validate_hand(hand)
                        
                        if is_valid:
                            successfully_parsed += 1
                            
                            # Verify tournament-specific fields
                            assert hand.game_format == "tournament"
                            assert hand.tournament_info is not None
                            assert "tournament_id" in hand.tournament_info
                        
            except Exception as e:
                print(f"Tournament hand parsing error: {e}")
        
        accuracy = (successfully_parsed / len(tournament_hands)) * 100
        print(f"Tournament hand accuracy: {accuracy:.2f}%")
        
        assert accuracy >= 99.0, f"Tournament hand accuracy {accuracy:.2f}% below requirement"
    
    async def test_cash_game_accuracy(self):
        """Test accuracy for cash game hands specifically."""
        parser = PokerStarsParser()
        
        cash_hands = [
            """PokerStars Hand #345678901: Hold'em No Limit ($0.25/$0.50 USD) - 2024/01/15 20:00:00 ET
Table 'CashTable' 6-max Seat #3 is the button
Seat 1: Player1 ($50.00 in chips)
Seat 2: Player2 ($47.75 in chips)
Seat 3: Player3 ($62.25 in chips)
Player1: posts small blind $0.25
Player2: posts big blind $0.50
*** HOLE CARDS ***
Dealt to Player1 [Js Jh]
Player3: raises $1.50 to $2.00
Player1: calls $1.75
Player2: folds
*** FLOP *** [Tc 5d 2h]
Player1: checks
Player3: bets $3.00
Player1: calls $3.00
*** TURN *** [Tc 5d 2h] [Jd]
Player1: checks
Player3: bets $6.00
Player1: raises $12.00 to $18.00
Player3: folds
Uncalled bet ($12.00) returned to Player1
Player1 collected $21.50 from pot
*** SUMMARY ***
Total pot $22.50 | Rake $1.00
Board [Tc 5d 2h Jd]
Seat 1: Player1 (small blind) collected ($21.50)
Seat 2: Player2 (big blind) folded before Flop
Seat 3: Player3 (button) folded on the Turn""",
            
            """PokerStars Hand #456789012: Hold'em No Limit ($1/$2 USD) - 2024/01/15 20:05:00 ET
Table 'HighStakes' 9-max Seat #5 is the button
Seat 1: Player1 ($200.00 in chips)
Seat 5: Player5 ($180.50 in chips)
Seat 9: Player9 ($220.75 in chips)
Player9: posts small blind $1
Player1: posts big blind $2
*** HOLE CARDS ***
Dealt to Player1 [Ad Ah]
Player5: raises $6 to $8
Player9: folds
Player1: raises $20 to $28
Player5: calls $20
*** FLOP *** [8h 3c 2s]
Player1: bets $35
Player5: calls $35
*** TURN *** [8h 3c 2s] [Kd]
Player1: bets $75
Player5: folds
Uncalled bet ($75) returned to Player1
Player1 collected $123.00 from pot
*** SUMMARY ***
Total pot $127.00 | Rake $4.00
Board [8h 3c 2s Kd]
Seat 1: Player1 (big blind) collected ($123.00)
Seat 5: Player5 (button) folded on the Turn
Seat 9: Player9 (small blind) folded before Flop"""
        ]
        
        successfully_parsed = 0
        
        for hand_text in cash_hands:
            try:
                if parser.can_parse(hand_text):
                    parsed_hands = parser.parse_hands(hand_text)
                    
                    if parsed_hands:
                        hand = parsed_hands[0]
                        is_valid = parser.validate_hand(hand)
                        
                        if is_valid:
                            successfully_parsed += 1
                            
                            # Verify cash game-specific fields
                            assert hand.game_format == "cash"
                            assert hand.blinds is not None
                            assert "small" in hand.blinds
                            assert "big" in hand.blinds
                            assert hand.rake is not None
                        
            except Exception as e:
                print(f"Cash game hand parsing error: {e}")
        
        accuracy = (successfully_parsed / len(cash_hands)) * 100
        print(f"Cash game hand accuracy: {accuracy:.2f}%")
        
        assert accuracy >= 99.0, f"Cash game hand accuracy {accuracy:.2f}% below requirement"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])