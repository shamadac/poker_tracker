"""
Pytest configuration for async tests.
"""
import pytest
import asyncio
import warnings

# Suppress specific warnings that occur during test cleanup
warnings.filterwarnings("ignore", message="Exception ignored.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

def pytest_configure(config):
    """Configure pytest settings."""
    # Set asyncio mode to auto
    config.option.asyncio_mode = "auto"

def pytest_sessionfinish(session, exitstatus):
    """Clean up after test session."""
    # Force garbage collection
    import gc
    gc.collect()
    
    # Close any remaining asyncio tasks
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except RuntimeError:
        pass  # No event loop running