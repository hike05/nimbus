#!/usr/bin/env python3
"""
Unit test runner for stealth VPN server.
Runs all unit tests and generates a summary report.
"""

import sys
import subprocess
from pathlib import Path


def run_test_file(test_file):
    """Run a single test file and return results."""
    print(f"\n{'=' * 60}")
    print(f"Running: {test_file.name}")
    print('=' * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=False,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"✗ Test timed out: {test_file.name}")
        return False
    except Exception as e:
        print(f"✗ Error running test: {e}")
        return False


def main():
    """Run all unit tests."""
    print("=" * 60)
    print("Stealth VPN Server - Unit Test Suite")
    print("=" * 60)
    
    # Find all test files
    test_dir = Path(__file__).parent / "unit"
    test_files = sorted(test_dir.glob("test_*.py"))
    
    if not test_files:
        print("No test files found!")
        return False
    
    print(f"\nFound {len(test_files)} test file(s)")
    
    # Run each test file
    results = []
    for test_file in test_files:
        success = run_test_file(test_file)
        results.append((test_file.name, success))
    
    # Print overall summary
    print("\n" + "=" * 60)
    print("Overall Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} test files passed")
    
    if passed == total:
        print("\n✓ All unit tests passed!")
        return True
    else:
        print(f"\n✗ {total - passed} test file(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
