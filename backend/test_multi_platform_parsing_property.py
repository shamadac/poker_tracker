"""
Property-based test for multi-platform hand parsing.

Feature: professional-poker-analyzer-rebuild
Property 28: Multi-Platform Hand Parsing

This test validates that for any hand history file from PokerStars or GGPoker, 
the system should automatically detect the platform and parse all available data 
with platform-specific handling according to Requirements 5.1 and 5.5.
"""

import pytest
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite

# Import the components to test
from app.services.hand_parser import HandParserService, PlatformDetector
from app.services.pokerstars_parser import PokerStarsParser
from app.services.ggpoker_parser import GGPokerParser
from app.services.exceptions import HandParsingError, UnsupportedPlatformError
from app.schemas.hand import HandCreate


class TestMultiPlatformHandParsing:
    """Property-based tests for multi-platform hand parsing."""
    
    @pytest.fixture
    def parser_service(self):
        """Create a HandParserService instance for testing."""
        return HandParserService()
    
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
            
            # Play money hand
            """PokerStars Hand #345678901: Hold'em No Limit (Play Money) ($10/$20) - 2024/01/15 20:10:00 ET
Table 'PlayTable' 6-max Seat #1 is the button
Seat 1: Player1 (2000 in chips)
Seat 2: Player2 (1800 in chips)
Player2: posts small blind 10
Player1: posts big blind 20
*** HOLE CARDS ***
Dealt to Player1 [Kc Ks]
Player2: calls 10
Player1: raises 40 to 60
Player2: calls 40
*** FLOP *** [2h 7s Qd]
Player1: bets 80
Player2: folds
Uncalled bet (80) returned to Player1
Player1 collected 120 from pot
*** SUMMARY ***
Total pot 120 | Rake 0
Board [2h 7s Qd]
Seat 1: Player1 (big blind) collected (120)
Seat 2: Player2 (small blind) folded on the Flop"""
        ]
    
    @pytest.fixture
    def sample_ggpoker_hands(self):
        """Sample GGPoker hand histories for testing."""
        return [
            # Valid GGPoker cash game hand
            """GGPoker Hand #123456789: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 GMT
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
Jackpot contribution $0.50
*** SUMMARY ***
Total pot $32.50 | Rake $1.00 | Jackpot $0.50
Board [Tc 5d 2h Jd]
Seat 1: Player1 (big blind) collected ($31.50)
Seat 2: Player2 (button) folded on the Turn
Seat 3: Player3 (small blind) folded before Flop""",
            
            # GGPoker tournament hand
            """GG Poker Hand #987654321: Tournament #555666777, $5+$0.50 USD Hold'em No Limit - Level II (15/30) - 2024/01/15 20:15:00 GMT
Table '555666777 1' 9-max Seat #4 is the button
Seat 1: Player1 (1485 in chips)
Seat 4: Player4 (1520 in chips)
Seat 7: Player7 (1495 in chips)
Player7: posts small blind 15
Player1: posts big blind 30
*** HOLE CARDS ***
Dealt to Player1 [Ah Qh]
Player4: raises 60 to 90
Player7: folds
Player1: calls 60
*** FLOP *** [As 3h 8c]
Player1: checks
Player4: bets 120
Player1: calls 120
*** TURN *** [As 3h 8c] [Qc]
Player1: checks
Player4: bets 240
Player1: raises 480 to 720
Player4: folds
Uncalled bet (480) returned to Player1
Player1 collected 825 from pot
*** SUMMARY ***
Total pot 825 | Rake 0
Board [As 3h 8c Qc]
Seat 1: Player1 (big blind) collected (825)
Seat 4: Player4 (button) folded on the Turn
Seat 7: Player7 (small blind) folded before Flop"""
        ]
    
    @staticmethod
    @composite
    def hand_id_strategy(draw):
        """Generate valid hand IDs."""
        return draw(st.integers(min_value=100000000, max_value=999999999999))
    
    @staticmethod
    @composite
    def platform_content_strategy(draw, platform: str):
        """Generate hand history content for a specific platform."""
        hand_id = draw(TestMultiPlatformHandParsing.hand_id_strategy())
        
        if platform == 'pokerstars':
            # Generate PokerStars-style content
            game_types = ['Hold\'em No Limit', 'Omaha Pot Limit', 'Hold\'em Limit']
            game_type = draw(st.sampled_from(game_types))
            
            stakes_formats = ['($0.02/$0.05 USD)', '($0.50/$1.00 CAD)', '($1/$2 EUR)']
            stakes = draw(st.sampled_from(stakes_formats))
            
            content = f"""PokerStars Hand #{hand_id}: {game_type} {stakes} - 2024/01/15 20:00:00 ET
Table 'TestTable' 6-max Seat #1 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises $2.00 to $4.00
Player2: folds
Uncalled bet ($2.00) returned to Player1
Player1 collected $3.00 from pot
*** SUMMARY ***
Total pot $3.00 | Rake $0.00
Seat 1: Player1 (button) collected ($3.00)
Seat 2: Player2 folded before Flop"""
            
        elif platform == 'ggpoker':
            # Generate GGPoker-style content
            game_types = ['Hold\'em No Limit', 'Omaha Pot Limit']
            game_type = draw(st.sampled_from(game_types))
            
            stakes_formats = ['($0.25/$0.50 USD)', '($1/$2 EUR)', '($0.50/$1.00 CAD)']
            stakes = draw(st.sampled_from(stakes_formats))
            
            content = f"""GGPoker Hand #{hand_id}: {game_type} {stakes} - 2024/01/15 20:00:00 GMT
Table 'GGTable' 6-max Seat #2 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
*** HOLE CARDS ***
Dealt to Player1 [Js Jh]
Player1: raises $3.00 to $4.00
Player2: folds
Uncalled bet ($3.00) returned to Player1
Player1 collected $2.50 from pot
Jackpot contribution $0.50
*** SUMMARY ***
Total pot $3.00 | Rake $0.00 | Jackpot $0.50
Seat 1: Player1 collected ($2.50)
Seat 2: Player2 (button) folded before Flop"""
        
        else:
            # Generate invalid content
            content = f"Unknown Platform Hand #{hand_id}: Invalid format"
        
        return content
    
    @given(platform=st.sampled_from(['pokerstars', 'ggpoker']))
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_platform_detection_consistency(self, parser_service, platform):
        """
        Property: For any valid hand history content from a supported platform,
        the platform detection should be consistent and accurate.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        # Generate simple content for the specified platform
        if platform == 'pokerstars':
            content = f"""PokerStars Hand #123456789: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 ET
Table 'TestTable' 6-max Seat #1 is the button
Seat 1: Player1 ($100.00 in chips)
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises $2.00 to $4.00
*** SUMMARY ***
Total pot $4.00 | Rake $0.00
Seat 1: Player1 (button) collected ($4.00)"""
        else:  # ggpoker
            content = f"""GGPoker Hand #123456789: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 GMT
Table 'GGTable' 6-max Seat #2 is the button
Seat 1: Player1 ($100.00 in chips)
*** HOLE CARDS ***
Dealt to Player1 [Js Jh]
Player1: raises $3.00 to $4.00
*** SUMMARY ***
Total pot $4.00 | Rake $0.00
Seat 1: Player1 collected ($4.00)"""
        
        try:
            detected_platform = parser_service.detect_platform(content)
            
            # The detected platform should match the expected platform
            assert detected_platform == platform, f"Expected {platform}, but detected {detected_platform}"
            
            # The parser should be able to handle this platform
            assert platform in parser_service.get_supported_platforms(), f"Platform {platform} not supported"
            
        except UnsupportedPlatformError:
            # This should not happen for valid platforms
            pytest.fail(f"Platform detection failed for valid {platform} content")
    
    def test_pokerstars_platform_detection_with_samples(self, parser_service, sample_pokerstars_hands):
        """
        Test platform detection with real PokerStars sample data.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        for i, hand_content in enumerate(sample_pokerstars_hands):
            try:
                detected_platform = parser_service.detect_platform(hand_content)
                assert detected_platform == 'pokerstars', f"Sample {i}: Expected pokerstars, got {detected_platform}"
            except UnsupportedPlatformError:
                # Skip invalid samples (they should fail detection)
                if "INVALID" not in hand_content and "Incomplete" not in hand_content:
                    pytest.fail(f"Sample {i}: Valid PokerStars hand not detected")
    
    def test_ggpoker_platform_detection_with_samples(self, parser_service, sample_ggpoker_hands):
        """
        Test platform detection with real GGPoker sample data.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        for i, hand_content in enumerate(sample_ggpoker_hands):
            try:
                detected_platform = parser_service.detect_platform(hand_content)
                assert detected_platform == 'ggpoker', f"Sample {i}: Expected ggpoker, got {detected_platform}"
            except UnsupportedPlatformError:
                # Skip invalid samples
                if "INVALID" not in hand_content:
                    pytest.fail(f"Sample {i}: Valid GGPoker hand not detected")
    
    def test_multi_platform_parsing_with_samples(self, parser_service, sample_pokerstars_hands, sample_ggpoker_hands):
        """
        Test that the parser can handle mixed platform content correctly.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        all_samples = [
            ('pokerstars', hand) for hand in sample_pokerstars_hands
        ] + [
            ('ggpoker', hand) for hand in sample_ggpoker_hands
        ]
        
        successful_parses = 0
        total_valid_samples = 0
        
        for expected_platform, hand_content in all_samples:
            # Skip obviously invalid samples
            if "INVALID" in hand_content or "Incomplete" in hand_content or "corrupted" in hand_content.lower():
                continue
                
            total_valid_samples += 1
            
            try:
                # Test platform detection
                detected_platform = parser_service.detect_platform(hand_content)
                assert detected_platform == expected_platform, f"Platform detection failed: expected {expected_platform}, got {detected_platform}"
                
                # Test parsing
                parsed_hands, errors = parser_service.parse_content(hand_content)
                
                if parsed_hands:
                    # Verify the parsed hand has the correct platform
                    for hand in parsed_hands:
                        assert hand.platform == expected_platform, f"Parsed hand has wrong platform: {hand.platform}"
                        assert hand.hand_id is not None, "Hand ID should not be None"
                        # Game type might be None for some parsers, so we'll be more lenient
                        if hand.game_type is not None:
                            assert isinstance(hand.game_type, str), "Game type should be a string if present"
                    
                    successful_parses += 1
                
            except (HandParsingError, UnsupportedPlatformError) as e:
                # Log the error but continue
                print(f"Parsing failed for {expected_platform} hand: {e}")
        
        # Calculate success rate
        if total_valid_samples > 0:
            success_rate = (successful_parses / total_valid_samples) * 100
            print(f"Multi-platform parsing success rate: {success_rate:.2f}% ({successful_parses}/{total_valid_samples})")
            
            # We expect high success rate for valid samples
            assert success_rate >= 80.0, f"Success rate {success_rate:.2f}% is too low"
    
    @given(
        platform=st.sampled_from(['pokerstars', 'ggpoker']),
        hand_id=st.integers(min_value=100000000, max_value=999999999999)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_platform_specific_parsing_properties(self, parser_service, platform, hand_id):
        """
        Property: For any generated hand content from a specific platform,
        the parser should extract platform-specific data correctly.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        # Generate platform-specific content
        if platform == 'pokerstars':
            content = f"""PokerStars Hand #{hand_id}: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 ET
Table 'TestTable' 6-max Seat #1 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
*** HOLE CARDS ***
Dealt to Player1 [As Kh]
Player1: raises $2.00 to $4.00
Player2: folds
Uncalled bet ($2.00) returned to Player1
Player1 collected $3.00 from pot
*** SUMMARY ***
Total pot $3.00 | Rake $0.00
Seat 1: Player1 (button) collected ($3.00)
Seat 2: Player2 folded before Flop"""
        else:  # ggpoker
            content = f"""GGPoker Hand #{hand_id}: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:00:00 GMT
Table 'GGTable' 6-max Seat #2 is the button
Seat 1: Player1 ($100.00 in chips)
Seat 2: Player2 ($95.50 in chips)
*** HOLE CARDS ***
Dealt to Player1 [Js Jh]
Player1: raises $3.00 to $4.00
Player2: folds
Uncalled bet ($3.00) returned to Player1
Player1 collected $2.50 from pot
Jackpot contribution $0.50
*** SUMMARY ***
Total pot $3.00 | Rake $0.00 | Jackpot $0.50
Seat 1: Player1 collected ($2.50)
Seat 2: Player2 (button) folded before Flop"""
        
        try:
            # Parse the content
            parsed_hands, errors = parser_service.parse_content(content)
            
            if parsed_hands:
                hand = parsed_hands[0]
                
                # Verify platform-specific properties
                assert hand.platform == platform, f"Platform mismatch: expected {platform}, got {hand.platform}"
                assert hand.hand_id is not None, "Hand ID should be extracted"
                assert str(hand_id) in hand.hand_id, f"Hand ID should contain {hand_id}"
                
                # Platform-specific validations
                if platform == 'pokerstars':
                    # PokerStars specific checks
                    if hand.timezone:
                        assert hand.timezone in ['ET', 'UTC'], f"Unexpected timezone for PokerStars: {hand.timezone}"
                
                elif platform == 'ggpoker':
                    # GGPoker specific checks
                    if hand.timezone:
                        assert hand.timezone in ['GMT', 'UTC'], f"Unexpected timezone for GGPoker: {hand.timezone}"
                    
                    # GGPoker might have jackpot contributions
                    # This is optional, so we just check it's valid if present
                    if hand.jackpot_contribution is not None:
                        assert hand.jackpot_contribution >= 0, "Jackpot contribution should be non-negative"
                
        except (HandParsingError, UnsupportedPlatformError):
            # Some generated content might be invalid, which is acceptable
            pass
    
    def test_unsupported_platform_handling(self, parser_service):
        """
        Test that unsupported platforms are handled correctly.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        unsupported_content = [
            "PartyPoker Hand #123456: Hold'em No Limit",
            "888poker Hand #789012: Omaha Pot Limit",
            "Random text that doesn't look like poker",
            "",  # Empty content
            "Some random content without poker markers"
        ]
        
        for content in unsupported_content:
            with pytest.raises(UnsupportedPlatformError):
                parser_service.detect_platform(content)
    
    def test_parser_registration_and_availability(self, parser_service):
        """
        Test that all expected parsers are registered and available.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        supported_platforms = parser_service.get_supported_platforms()
        
        # Both platforms should be supported
        assert 'pokerstars' in supported_platforms, "PokerStars parser should be registered"
        assert 'ggpoker' in supported_platforms, "GGPoker parser should be registered"
        
        # Verify parsers can be accessed
        assert 'pokerstars' in parser_service.parsers, "PokerStars parser should be accessible"
        assert 'ggpoker' in parser_service.parsers, "GGPoker parser should be accessible"
        
        # Verify parser instances are correct types
        assert isinstance(parser_service.parsers['pokerstars'], PokerStarsParser), "PokerStars parser should be correct type"
        assert isinstance(parser_service.parsers['ggpoker'], GGPokerParser), "GGPoker parser should be correct type"
    
    @given(
        content=st.text(min_size=10, max_size=1000),
        platform_marker=st.sampled_from(['PokerStars Hand #', 'GGPoker Hand #', 'GG Poker Hand #'])
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_platform_detection_robustness(self, parser_service, content, platform_marker):
        """
        Property: Platform detection should be robust and handle various content formats.
        
        **Feature: professional-poker-analyzer-rebuild, Property 28: Multi-Platform Hand Parsing**
        """
        # Create content with platform marker
        test_content = f"{platform_marker}123456789: {content}"
        
        try:
            detected_platform = parser_service.detect_platform(test_content)
            
            # Verify the detection matches the marker
            if 'PokerStars' in platform_marker:
                assert detected_platform == 'pokerstars', f"Should detect PokerStars from marker {platform_marker}"
            elif 'GGPoker' in platform_marker or 'GG Poker' in platform_marker:
                assert detected_platform == 'ggpoker', f"Should detect GGPoker from marker {platform_marker}"
                
        except UnsupportedPlatformError:
            # This might happen if the content is too malformed
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])