#!/usr/bin/env python3
"""
Test runner with proper cleanup for async tests.
"""
import subprocess
import sys
import signal
import os
import time

def run_tests_with_timeout():
    """Run tests with timeout and proper cleanup."""
    try:
        # Run pytest with timeout
        process = subprocess.Popen([
            sys.executable, "-m", "pytest", 
            "test_statistics_service.py", 
            "-v", 
            "--tb=short",
            "--asyncio-mode=auto"
        ], cwd=os.path.dirname(__file__))
        
        # Wait for completion with timeout
        try:
            return_code = process.wait(timeout=60)  # 60 second timeout
            return return_code
        except subprocess.TimeoutExpired:
            print("Tests timed out, terminating...")
            process.terminate()
            time.sleep(2)
            if process.poll() is None:
                process.kill()
            return 1
            
    except KeyboardInterrupt:
        print("Interrupted by user")
        if 'process' in locals():
            process.terminate()
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests_with_timeout()
    sys.exit(exit_code)