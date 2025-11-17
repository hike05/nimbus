#!/usr/bin/env python3
"""
Integration test runner for stealth VPN server.
Runs all integration tests and generates a summary report.
"""

import sys
import subprocess
from pathlib import Path

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def check_docker_running():
    """Check if Docker is running before tests."""
    try:
        result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def run_test_file(test_file):
    """Run a single test file and return results."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Running: {test_file.name}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=False,
            text=True,
            timeout=120  # Longer timeout for integration tests
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"{RED}✗ Test timed out: {test_file.name}{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ Error running test: {e}{NC}")
        return False


def main():
    """Run all integration tests."""
    print(f"{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Stealth VPN Server - Integration Test Suite{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    # Check Docker first
    if not check_docker_running():
        print(f"\n{RED}✗ Docker is not running!{NC}")
        print(f"{YELLOW}Please start Docker and ensure containers are running:{NC}")
        print(f"  docker compose up -d")
        return False
    
    print(f"\n{GREEN}✓ Docker is running{NC}")
    
    # Find all test files
    test_dir = Path(__file__).parent / "integration"
    test_files = sorted(test_dir.glob("test_*.py"))
    
    if not test_files:
        print(f"{RED}No test files found!{NC}")
        return False
    
    print(f"\nFound {len(test_files)} test file(s)")
    
    # Run each test file
    results = []
    for test_file in test_files:
        success = run_test_file(test_file)
        results.append((test_file.name, success))
    
    # Print overall summary
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Overall Test Summary{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        if success:
            print(f"{GREEN}✓ PASS{NC}: {test_name}")
        else:
            print(f"{RED}✗ FAIL{NC}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} test files passed")
    
    if passed == total:
        print(f"\n{GREEN}✓ All integration tests passed!{NC}")
        return True
    else:
        print(f"\n{YELLOW}⚠ {total - passed} test file(s) failed{NC}")
        print(f"{YELLOW}Check container logs with: docker compose logs{NC}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
