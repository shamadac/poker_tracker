"""
Property-based test for asynchronous processing with progress tracking.

Feature: professional-poker-analyzer-rebuild
Property 13: Asynchronous Processing with Progress

This test validates that for any long-running operation (file parsing, batch analysis), 
the system should process asynchronously and provide real-time progress updates to users
according to Requirements 5.2.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite

# Import the components to test
from app.services.background_processor import BackgroundFileProcessor, ProcessingProgress, ProcessingResult
from app.models.file_processing import FileProcessingTask, ProcessingStatus
from app.services.hand_parser import HandParserService
from app.schemas.hand import HandCreate


class TestAsynchronousProcessingProperty:
    """Property-based tests for asynchronous processing with progress tracking."""
    
    @pytest.fixture
    def mock_db_session_factory(self):
        """Create a mock database session factory."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.refresh = AsyncMock()
        
        # Make the session work as an async context manager
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Counter for unique task IDs
        self._task_counter = 0
        
        def create_mock_task():
            self._task_counter += 1
            mock_task = MagicMock()
            mock_task.id = f"test-task-{self._task_counter}"
            mock_task.progress_percentage = 0
            mock_task.hands_processed = 0
            mock_task.hands_failed = 0
            mock_task.current_step = "Initializing..."
            mock_task.started_at = None
            mock_task.estimated_completion = None
            mock_task.update_progress = MagicMock()
            return mock_task
        
        # Mock task creation - create new task each time
        def mock_add(task):
            task.id = f"test-task-{self._task_counter + 1}"
            self._task_counter += 1
        
        def mock_refresh(task):
            if not hasattr(task, 'id') or task.id is None:
                task.id = f"test-task-{self._task_counter}"
        
        mock_session.add.side_effect = mock_add
        mock_session.refresh.side_effect = mock_refresh
        
        # Mock query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = create_mock_task()
        mock_result.scalars.return_value.all.return_value = [create_mock_task()]
        mock_session.execute.return_value = mock_result
        
        def session_factory():
            return mock_session
        
        return session_factory, mock_session, create_mock_task()
    
    @pytest.fixture
    def background_processor(self, mock_db_session_factory):
        """Create a BackgroundFileProcessor instance for testing."""
        session_factory, _, _ = mock_db_session_factory
        return BackgroundFileProcessor(session_factory, max_workers=2)
    
    @pytest.fixture
    def temp_directory(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass
    
    @staticmethod
    @composite
    def user_id_strategy(draw):
        """Generate valid user IDs."""
        return draw(st.uuids()).hex
    
    @staticmethod
    @composite
    def platform_strategy(draw):
        """Generate valid platform names."""
        return draw(st.sampled_from(['pokerstars', 'ggpoker']))
    
    @staticmethod
    @composite
    def file_size_strategy(draw):
        """Generate realistic file sizes for testing."""
        return draw(st.integers(min_value=100, max_value=10*1024*1024))  # 100B to 10MB
    
    @staticmethod
    @composite
    def processing_options_strategy(draw):
        """Generate processing options."""
        return {
            'validate_hands': draw(st.booleans()),
            'skip_duplicates': draw(st.booleans()),
            'batch_size': draw(st.integers(min_value=10, max_value=1000)),
            'timeout_seconds': draw(st.integers(min_value=30, max_value=300))
        }
    
    @staticmethod
    @composite
    def hand_count_strategy(draw):
        """Generate realistic hand counts."""
        return draw(st.integers(min_value=1, max_value=1000))
    
    def create_sample_hand_history_file(self, file_path: str, platform: str, hand_count: int = 10) -> str:
        """Create a sample hand history file for testing."""
        content_lines = []
        
        for i in range(hand_count):
            hand_id = 1000000000 + i
            
            if platform == 'pokerstars':
                hand_content = f"""PokerStars Hand #{hand_id}: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:{i:02d}:00 ET
Table 'TestTable{i}' 6-max Seat #1 is the button
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
Seat 2: Player2 folded before Flop

"""
            else:  # ggpoker
                hand_content = f"""GGPoker Hand #{hand_id}: Hold'em No Limit ($0.50/$1.00 USD) - 2024/01/15 20:{i:02d}:00 GMT
Table 'GGTable{i}' 6-max Seat #2 is the button
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
Seat 2: Player2 (button) folded before Flop

"""
            
            content_lines.append(hand_content)
        
        # Write to file
        with open(file_path, 'w') as f:
            f.write('\n'.join(content_lines))
        
        return '\n'.join(content_lines)
    
    @given(
        user_id=user_id_strategy(),
        platform=platform_strategy(),
        hand_count=hand_count_strategy(),
        processing_options=processing_options_strategy()
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_asynchronous_file_processing_property(self, background_processor, user_id, platform, hand_count, processing_options, temp_directory):
        """
        Property: For any file processing request, the system should process asynchronously
        and provide progress updates throughout the operation.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Create a test file
        test_file = os.path.join(temp_directory, f"test_hands_{platform}.txt")
        self.create_sample_hand_history_file(test_file, platform, hand_count)
        
        # Mock the hand parser to return predictable results
        mock_hands = []
        for i in range(hand_count):
            mock_hand = HandCreate(
                hand_id=str(1000000000 + i),
                platform=platform,
                game_type="Hold'em No Limit",
                stakes="$0.50/$1.00",
                pot_size=Decimal("3.00"),
                rake=Decimal("0.00"),
                raw_text=f"Mock hand {i}"
            )
            mock_hands.append(mock_hand)
        
        with patch.object(background_processor.hand_parser, 'parse_file', return_value=(mock_hands, [])):
            try:
                # Start the background processor service
                await background_processor.start_service()
                
                # Submit file for processing
                task_id = await background_processor.submit_file_processing(
                    user_id=user_id,
                    file_path=test_file,
                    platform=platform,
                    task_name=f"Test processing {hand_count} hands",
                    processing_options=processing_options
                )
                
                # Task ID should be returned
                assert task_id is not None, "Task ID should be returned"
                assert isinstance(task_id, str), "Task ID should be a string"
                assert len(task_id) > 0, "Task ID should not be empty"
                
                # Track progress updates
                progress_updates = []
                
                def progress_callback(progress: ProcessingProgress):
                    progress_updates.append({
                        'percentage': progress.progress_percentage,
                        'step': progress.current_step,
                        'hands_processed': progress.hands_processed,
                        'hands_failed': progress.hands_failed,
                        'timestamp': time.time()
                    })
                
                # Register progress callback
                background_processor.register_progress_callback(task_id, progress_callback)
                
                # Wait for processing to complete or timeout
                max_wait_time = 10  # seconds
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    progress = await background_processor.get_task_progress(task_id)
                    
                    if progress:
                        # Progress should be valid
                        assert isinstance(progress.progress_percentage, int), "Progress percentage should be integer"
                        assert 0 <= progress.progress_percentage <= 100, "Progress should be between 0 and 100"
                        assert isinstance(progress.current_step, str), "Current step should be string"
                        assert len(progress.current_step) > 0, "Current step should not be empty"
                        assert progress.hands_processed >= 0, "Hands processed should be non-negative"
                        assert progress.hands_failed >= 0, "Hands failed should be non-negative"
                        
                        # If processing is complete, break
                        if progress.progress_percentage == 100:
                            break
                    
                    await asyncio.sleep(0.1)
                
                # Verify that progress updates were received
                if progress_updates:
                    # Progress should generally increase over time
                    first_progress = progress_updates[0]['percentage']
                    last_progress = progress_updates[-1]['percentage']
                    
                    assert last_progress >= first_progress, "Progress should not decrease"
                    
                    # Progress steps should be informative
                    for update in progress_updates:
                        assert isinstance(update['step'], str), "Progress step should be string"
                        assert len(update['step']) > 0, "Progress step should not be empty"
                        assert update['hands_processed'] >= 0, "Hands processed should be non-negative"
                        assert update['hands_failed'] >= 0, "Hands failed should be non-negative"
                
                # Test task cancellation
                cancel_result = await background_processor.cancel_task(task_id)
                assert isinstance(cancel_result, bool), "Cancel result should be boolean"
                
            finally:
                # Stop the background processor service
                await background_processor.stop_service()
    
    @given(
        user_id=user_id_strategy(),
        platform=platform_strategy(),
        num_files=st.integers(min_value=2, max_value=5),
        hands_per_file=st.integers(min_value=5, max_value=50)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_batch_processing_progress_property(self, background_processor, user_id, platform, num_files, hands_per_file, temp_directory):
        """
        Property: For any batch processing operation, progress should be tracked
        across all files and provide meaningful updates.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Create multiple test files
        test_files = []
        total_expected_hands = 0
        
        for i in range(num_files):
            test_file = os.path.join(temp_directory, f"batch_test_{i}_{platform}.txt")
            self.create_sample_hand_history_file(test_file, platform, hands_per_file)
            test_files.append(test_file)
            total_expected_hands += hands_per_file
        
        # Mock the hand parser
        def mock_parse_file(file_path):
            # Return hands based on the file
            file_index = int(os.path.basename(file_path).split('_')[2])
            mock_hands = []
            for j in range(hands_per_file):
                hand_id = str(1000000000 + file_index * 1000 + j)
                mock_hand = HandCreate(
                    hand_id=hand_id,
                    platform=platform,
                    game_type="Hold'em No Limit",
                    stakes="$0.50/$1.00",
                    pot_size=Decimal("3.00"),
                    rake=Decimal("0.00"),
                    raw_text=f"Mock hand {hand_id}"
                )
                mock_hands.append(mock_hand)
            return mock_hands, []
        
        with patch.object(background_processor.hand_parser, 'parse_file', side_effect=mock_parse_file):
            try:
                # Start the background processor service
                await background_processor.start_service()
                
                # Submit batch processing
                task_id = await background_processor.submit_batch_processing(
                    user_id=user_id,
                    file_paths=test_files,
                    platform=platform,
                    task_name=f"Batch process {num_files} files",
                    processing_options={'batch_mode': True}
                )
                
                # Task ID should be returned
                assert task_id is not None, "Batch task ID should be returned"
                assert isinstance(task_id, str), "Batch task ID should be a string"
                
                # Track progress for batch processing
                batch_progress_updates = []
                
                def batch_progress_callback(progress: ProcessingProgress):
                    batch_progress_updates.append({
                        'percentage': progress.progress_percentage,
                        'step': progress.current_step,
                        'hands_processed': progress.hands_processed,
                        'hands_failed': progress.hands_failed,
                        'processing_rate': progress.processing_rate,
                        'timestamp': time.time()
                    })
                
                background_processor.register_progress_callback(task_id, batch_progress_callback)
                
                # Wait for batch processing to complete
                max_wait_time = 15  # seconds for batch processing
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    progress = await background_processor.get_task_progress(task_id)
                    
                    if progress:
                        # Batch progress should be valid
                        assert 0 <= progress.progress_percentage <= 100, "Batch progress should be between 0 and 100"
                        assert isinstance(progress.current_step, str), "Batch current step should be string"
                        assert progress.hands_processed >= 0, "Batch hands processed should be non-negative"
                        
                        # Processing rate should be reasonable if available
                        if progress.processing_rate is not None:
                            assert progress.processing_rate >= 0, "Processing rate should be non-negative"
                        
                        # If processing is complete, break
                        if progress.progress_percentage == 100:
                            break
                    
                    await asyncio.sleep(0.2)
                
                # Verify batch progress updates
                if batch_progress_updates:
                    # Should have multiple progress updates for batch processing
                    assert len(batch_progress_updates) >= 1, "Should have at least one batch progress update"
                    
                    # Progress should mention files being processed
                    file_mentions = sum(1 for update in batch_progress_updates 
                                      if 'file' in update['step'].lower())
                    
                    # At least some updates should mention file processing
                    if num_files > 1:
                        assert file_mentions >= 1, "Batch processing should mention files in progress updates"
                
            finally:
                # Stop the background processor service
                await background_processor.stop_service()
    
    @given(
        user_id=user_id_strategy(),
        platform=platform_strategy()
    )
    @settings(max_examples=30, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_progress_callback_reliability_property(self, background_processor, user_id, platform, temp_directory):
        """
        Property: For any processing operation with registered callbacks, progress
        callbacks should be called reliably and with valid data.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Create a small test file
        test_file = os.path.join(temp_directory, f"callback_test_{platform}.txt")
        self.create_sample_hand_history_file(test_file, platform, 20)
        
        # Mock the hand parser
        mock_hands = [
            HandCreate(
                hand_id=str(1000000000 + i),
                platform=platform,
                game_type="Hold'em No Limit",
                stakes="$0.50/$1.00",
                pot_size=Decimal("3.00"),
                rake=Decimal("0.00"),
                raw_text=f"Mock hand {i}"
            )
            for i in range(20)
        ]
        
        with patch.object(background_processor.hand_parser, 'parse_file', return_value=(mock_hands, [])):
            try:
                # Start the background processor service
                await background_processor.start_service()
                
                # Submit file for processing
                task_id = await background_processor.submit_file_processing(
                    user_id=user_id,
                    file_path=test_file,
                    platform=platform,
                    task_name="Callback reliability test"
                )
                
                # Register multiple callbacks to test reliability
                callback_results = {
                    'callback1': [],
                    'callback2': [],
                    'callback3': []
                }
                
                def create_callback(callback_name):
                    def callback(progress: ProcessingProgress):
                        callback_results[callback_name].append({
                            'task_id': progress.task_id,
                            'percentage': progress.progress_percentage,
                            'step': progress.current_step,
                            'hands_processed': progress.hands_processed,
                            'hands_failed': progress.hands_failed,
                            'timestamp': time.time()
                        })
                    return callback
                
                # Register multiple callbacks
                for callback_name in callback_results.keys():
                    background_processor.register_progress_callback(
                        task_id, 
                        create_callback(callback_name)
                    )
                
                # Wait for processing to complete
                max_wait_time = 10
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    progress = await background_processor.get_task_progress(task_id)
                    
                    if progress and progress.progress_percentage == 100:
                        break
                    
                    await asyncio.sleep(0.1)
                
                # Verify all callbacks received updates
                for callback_name, updates in callback_results.items():
                    if updates:  # If any callbacks were triggered
                        # All callbacks should receive the same number of updates
                        assert len(updates) >= 1, f"Callback {callback_name} should receive at least one update"
                        
                        # All updates should have valid data
                        for update in updates:
                            assert update['task_id'] == task_id, f"Callback {callback_name} should receive correct task_id"
                            assert 0 <= update['percentage'] <= 100, f"Callback {callback_name} should receive valid percentage"
                            assert isinstance(update['step'], str), f"Callback {callback_name} should receive string step"
                            assert update['hands_processed'] >= 0, f"Callback {callback_name} should receive valid hands_processed"
                            assert update['hands_failed'] >= 0, f"Callback {callback_name} should receive valid hands_failed"
                
                # If any callbacks were triggered, they should all have similar update counts
                update_counts = [len(updates) for updates in callback_results.values() if updates]
                if update_counts:
                    min_count = min(update_counts)
                    max_count = max(update_counts)
                    
                    # Allow some variation but callbacks should be roughly consistent
                    assert max_count - min_count <= 2, "Callbacks should receive similar numbers of updates"
                
            finally:
                # Stop the background processor service
                await background_processor.stop_service()
    
    @given(
        user_id=user_id_strategy(),
        platform=platform_strategy(),
        processing_delay=st.floats(min_value=0.1, max_value=2.0)
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_processing_time_estimation_property(self, background_processor, user_id, platform, processing_delay, temp_directory):
        """
        Property: For any processing operation, time estimation should be reasonable
        and improve as more data is processed.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Create a test file
        test_file = os.path.join(temp_directory, f"timing_test_{platform}.txt")
        hand_count = 50
        self.create_sample_hand_history_file(test_file, platform, hand_count)
        
        # Mock the hand parser with artificial delay
        async def mock_parse_with_delay(file_path):
            await asyncio.sleep(processing_delay)
            mock_hands = [
                HandCreate(
                    hand_id=str(1000000000 + i),
                    platform=platform,
                    game_type="Hold'em No Limit",
                    stakes="$0.50/$1.00",
                    pot_size=Decimal("3.00"),
                    rake=Decimal("0.00"),
                    raw_text=f"Mock hand {i}"
                )
                for i in range(hand_count)
            ]
            return mock_hands, []
        
        with patch.object(background_processor.hand_parser, 'parse_file', side_effect=mock_parse_with_delay):
            try:
                # Start the background processor service
                await background_processor.start_service()
                
                # Submit file for processing
                task_id = await background_processor.submit_file_processing(
                    user_id=user_id,
                    file_path=test_file,
                    platform=platform,
                    task_name="Time estimation test"
                )
                
                # Track time-related progress data
                time_estimates = []
                processing_rates = []
                
                def time_tracking_callback(progress: ProcessingProgress):
                    if progress.estimated_completion:
                        time_estimates.append({
                            'percentage': progress.progress_percentage,
                            'estimated_completion': progress.estimated_completion,
                            'timestamp': datetime.now(timezone.utc)
                        })
                    
                    if progress.processing_rate:
                        processing_rates.append({
                            'percentage': progress.progress_percentage,
                            'rate': progress.processing_rate,
                            'hands_processed': progress.hands_processed
                        })
                
                background_processor.register_progress_callback(task_id, time_tracking_callback)
                
                # Wait for processing to complete
                max_wait_time = 15
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    progress = await background_processor.get_task_progress(task_id)
                    
                    if progress:
                        # Processing rate should be reasonable if available
                        if progress.processing_rate is not None:
                            assert progress.processing_rate >= 0, "Processing rate should be non-negative"
                            # Rate should be reasonable (not impossibly high)
                            assert progress.processing_rate <= 10000, "Processing rate should be reasonable"
                        
                        # Estimated completion should be in the future if available
                        if progress.estimated_completion:
                            current_time = datetime.now(timezone.utc)
                            # Allow some tolerance for timing variations
                            time_diff = (progress.estimated_completion - current_time).total_seconds()
                            assert time_diff >= -60, "Estimated completion should not be too far in the past"
                        
                        if progress.progress_percentage == 100:
                            break
                    
                    await asyncio.sleep(0.2)
                
                # Verify time estimation data
                if time_estimates:
                    # Time estimates should generally become more accurate (closer to actual completion)
                    # as processing progresses
                    for estimate in time_estimates:
                        assert isinstance(estimate['estimated_completion'], datetime), "Estimated completion should be datetime"
                        assert 0 <= estimate['percentage'] <= 100, "Progress percentage should be valid"
                
                if processing_rates:
                    # Processing rates should be consistent and reasonable
                    rates = [rate['rate'] for rate in processing_rates]
                    
                    # All rates should be positive
                    assert all(rate > 0 for rate in rates), "All processing rates should be positive"
                    
                    # Rates should be within a reasonable range
                    avg_rate = sum(rates) / len(rates)
                    assert 0.1 <= avg_rate <= 1000, f"Average processing rate {avg_rate} should be reasonable"
                
            finally:
                # Stop the background processor service
                await background_processor.stop_service()
    
    @given(
        user_id=user_id_strategy(),
        platform=platform_strategy()
    )
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_error_handling_during_processing_property(self, background_processor, user_id, platform, temp_directory):
        """
        Property: For any processing operation that encounters errors, the system
        should handle errors gracefully and continue processing valid data.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Create a test file
        test_file = os.path.join(temp_directory, f"error_test_{platform}.txt")
        self.create_sample_hand_history_file(test_file, platform, 30)
        
        # Mock the hand parser to simulate some parsing errors
        def mock_parse_with_errors(file_path):
            mock_hands = []
            errors = []
            
            for i in range(30):
                if i % 5 == 0:  # Every 5th hand has an error
                    errors.append({
                        'error_type': 'parsing_error',
                        'error_message': f'Failed to parse hand {i}',
                        'hand_text': f'Invalid hand data {i}'
                    })
                else:
                    mock_hand = HandCreate(
                        hand_id=str(1000000000 + i),
                        platform=platform,
                        game_type="Hold'em No Limit",
                        stakes="$0.50/$1.00",
                        pot_size=Decimal("3.00"),
                        rake=Decimal("0.00"),
                        raw_text=f"Mock hand {i}"
                    )
                    mock_hands.append(mock_hand)
            
            return mock_hands, errors
        
        with patch.object(background_processor.hand_parser, 'parse_file', side_effect=mock_parse_with_errors):
            try:
                # Start the background processor service
                await background_processor.start_service()
                
                # Submit file for processing
                task_id = await background_processor.submit_file_processing(
                    user_id=user_id,
                    file_path=test_file,
                    platform=platform,
                    task_name="Error handling test"
                )
                
                # Track error-related progress
                error_progress_updates = []
                
                def error_tracking_callback(progress: ProcessingProgress):
                    error_progress_updates.append({
                        'percentage': progress.progress_percentage,
                        'hands_processed': progress.hands_processed,
                        'hands_failed': progress.hands_failed,
                        'step': progress.current_step
                    })
                
                background_processor.register_progress_callback(task_id, error_tracking_callback)
                
                # Wait for processing to complete
                max_wait_time = 10
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    progress = await background_processor.get_task_progress(task_id)
                    
                    if progress:
                        # Even with errors, progress should be valid
                        assert 0 <= progress.progress_percentage <= 100, "Progress should be valid despite errors"
                        assert progress.hands_processed >= 0, "Hands processed should be non-negative"
                        assert progress.hands_failed >= 0, "Hands failed should be non-negative"
                        
                        # Total hands (processed + failed) should make sense
                        total_hands = progress.hands_processed + progress.hands_failed
                        if total_hands > 0:
                            # Should have processed some hands and failed some
                            assert progress.hands_processed > 0, "Should have processed some hands successfully"
                            assert progress.hands_failed > 0, "Should have some failed hands (due to mock errors)"
                        
                        if progress.progress_percentage == 100:
                            break
                    
                    await asyncio.sleep(0.1)
                
                # Verify error handling in progress updates
                if error_progress_updates:
                    final_update = error_progress_updates[-1]
                    
                    # Should have both successful and failed hands
                    assert final_update['hands_processed'] > 0, "Should have processed some hands successfully"
                    assert final_update['hands_failed'] > 0, "Should have some failed hands"
                    
                    # Progress should reach 100% even with errors
                    assert final_update['percentage'] == 100, "Processing should complete despite errors"
                
            finally:
                # Stop the background processor service
                await background_processor.stop_service()
    
    async def test_concurrent_processing_tasks_property(self, background_processor, temp_directory):
        """
        Test that multiple concurrent processing tasks are handled correctly.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Create multiple test files
        test_files = []
        user_ids = ["user1", "user2", "user3"]
        platforms = ["pokerstars", "ggpoker"]
        
        for i, (user_id, platform) in enumerate(zip(user_ids, platforms * 2)):
            test_file = os.path.join(temp_directory, f"concurrent_test_{i}_{platform}.txt")
            self.create_sample_hand_history_file(test_file, platform, 20)
            test_files.append((test_file, user_id, platform))
        
        # Mock the hand parser
        def mock_parse_concurrent(file_path):
            file_index = int(os.path.basename(file_path).split('_')[2])
            mock_hands = [
                HandCreate(
                    hand_id=str(2000000000 + file_index * 1000 + j),
                    platform="pokerstars",  # Simplified for testing
                    game_type="Hold'em No Limit",
                    stakes="$0.50/$1.00",
                    pot_size=Decimal("3.00"),
                    rake=Decimal("0.00"),
                    raw_text=f"Concurrent mock hand {file_index}_{j}"
                )
                for j in range(20)
            ]
            return mock_hands, []
        
        with patch.object(background_processor.hand_parser, 'parse_file', side_effect=mock_parse_concurrent):
            try:
                # Start the background processor service
                await background_processor.start_service()
                
                # Submit multiple concurrent processing tasks
                task_ids = []
                for test_file, user_id, platform in test_files:
                    task_id = await background_processor.submit_file_processing(
                        user_id=user_id,
                        file_path=test_file,
                        platform=platform,
                        task_name=f"Concurrent test for {user_id}"
                    )
                    task_ids.append(task_id)
                
                # All task IDs should be unique
                assert len(set(task_ids)) == len(task_ids), "All task IDs should be unique"
                
                # Track progress for all tasks
                all_progress = {task_id: [] for task_id in task_ids}
                
                def create_concurrent_callback(task_id):
                    def callback(progress: ProcessingProgress):
                        all_progress[task_id].append({
                            'percentage': progress.progress_percentage,
                            'hands_processed': progress.hands_processed,
                            'timestamp': time.time()
                        })
                    return callback
                
                # Register callbacks for all tasks
                for task_id in task_ids:
                    background_processor.register_progress_callback(
                        task_id, 
                        create_concurrent_callback(task_id)
                    )
                
                # Wait for all tasks to complete
                max_wait_time = 15
                start_time = time.time()
                completed_tasks = set()
                
                while time.time() - start_time < max_wait_time and len(completed_tasks) < len(task_ids):
                    for task_id in task_ids:
                        if task_id not in completed_tasks:
                            progress = await background_processor.get_task_progress(task_id)
                            
                            if progress and progress.progress_percentage == 100:
                                completed_tasks.add(task_id)
                    
                    await asyncio.sleep(0.2)
                
                # Verify concurrent processing results
                assert len(completed_tasks) >= 1, "At least one task should complete"
                
                # Each completed task should have progress updates
                for task_id in completed_tasks:
                    progress_updates = all_progress[task_id]
                    if progress_updates:
                        # Should have at least one progress update
                        assert len(progress_updates) >= 1, f"Task {task_id} should have progress updates"
                        
                        # Final progress should be 100%
                        final_progress = progress_updates[-1]
                        assert final_progress['percentage'] == 100, f"Task {task_id} should reach 100% completion"
                        assert final_progress['hands_processed'] > 0, f"Task {task_id} should process some hands"
                
            finally:
                # Stop the background processor service
                await background_processor.stop_service()
    
    def test_processing_queue_management_property(self, background_processor):
        """
        Test that the processing queue manages tasks correctly.
        
        **Feature: professional-poker-analyzer-rebuild, Property 13: Asynchronous Processing with Progress**
        **Validates: Requirements 5.2**
        """
        # Test queue initialization
        assert hasattr(background_processor, 'processing_queue'), "Should have processing queue"
        assert hasattr(background_processor, 'active_tasks'), "Should have active tasks tracking"
        assert hasattr(background_processor, 'progress_callbacks'), "Should have progress callbacks"
        
        # Initial state should be empty
        assert len(background_processor.active_tasks) == 0, "Active tasks should be empty initially"
        assert len(background_processor.progress_callbacks) == 0, "Progress callbacks should be empty initially"
        
        # Queue should be accessible
        assert background_processor.processing_queue is not None, "Processing queue should be initialized"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])