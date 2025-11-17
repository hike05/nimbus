#!/usr/bin/env python3
"""
Master test runner for stealth VPN server.
Runs both unit and integration tests with comprehensive reporting.
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'  # No Color


def print_header(text):
    """Print a formatted header."""
    print(f"\n{CYAN}{'=' * 70}{NC}")
    print(f"{CYAN}{text.center(70)}{NC}")
    print(f"{CYAN}{'=' * 70}{NC}\n")


def run_test_suite(suite_name, script_path):
    """Run a test suite and return results."""
    print_header(f"Running {suite_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"{RED}✗ {suite_name} timed out{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ Error running {suite_name}: {e}{NC}")
        return False


def check_prerequisites():
    """Check if prerequisites are met."""
    print_header("Checking Prerequisites")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 7):
        issues.append("Python 3.7+ required")
    else:
        print(f"{GREEN}✓ Python version: {sys.version.split()[0]}{NC}")
    
    # Check if Docker is available
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"{GREEN}✓ Docker is available{NC}")
        else:
            issues.append("Docker not available")
    except:
        issues.append("Docker not found")
    
    # Check if test directories exist
    test_dir = Path(__file__).parent
    if not (test_dir / 'unit').exists():
        issues.append("Unit test directory not found")
    else:
        print(f"{GREEN}✓ Unit test directory exists{NC}")
    
    if not (test_dir / 'integration').exists():
        issues.append("Integration test directory not found")
    else:
        print(f"{GREEN}✓ Integration test directory exists{NC}")
    
    if issues:
        print(f"\n{RED}Prerequisites not met:{NC}")
        for issue in issues:
            print(f"  {RED}✗ {issue}{NC}")
        return False
    
    return True


def generate_report(results, start_time, end_time):
    """Generate a test report."""
    print_header("Test Report")
    
    duration = (end_time - start_time).total_seconds()
    
    print(f"Test Duration: {duration:.2f} seconds")
    print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for suite_name, success in results:
        if success:
            print(f"{GREEN}✓ PASS{NC}: {suite_name}")
        else:
            print(f"{RED}✗ FAIL{NC}: {suite_name}")
    
    print(f"\n{BLUE}Total: {passed}/{total} test suites passed{NC}")
    
    if passed == total:
        print(f"\n{GREEN}{'=' * 70}{NC}")
        print(f"{GREEN}{'✓ ALL TESTS PASSED!'.center(70)}{NC}")
        print(f"{GREEN}{'=' * 70}{NC}\n")
        return True
    else:
        print(f"\n{RED}{'=' * 70}{NC}")
        print(f"{RED}{f'✗ {total - passed} TEST SUITE(S) FAILED'.center(70)}{NC}")
        print(f"{RED}{'=' * 70}{NC}\n")
        return False


def main():
    """Run all test suites."""
    print(f"{CYAN}{'=' * 70}{NC}")
    print(f"{CYAN}{'Stealth VPN Server - Comprehensive Test Suite'.center(70)}{NC}")
    print(f"{CYAN}{'=' * 70}{NC}")
    
    # Check prerequisites
    if not check_prerequisites():
        print(f"\n{RED}Cannot proceed with tests due to missing prerequisites{NC}")
        return False
    
    start_time = datetime.now()
    
    # Define test suites
    test_dir = Path(__file__).parent
    test_suites = [
        ("Unit Tests", test_dir / "run_unit_tests.py"),
        ("Integration Tests", test_dir / "run_integration_tests.py"),
    ]
    
    # Run each test suite
    results = []
    for suite_name, script_path in test_suites:
        if script_path.exists():
            success = run_test_suite(suite_name, script_path)
            results.append((suite_name, success))
        else:
            print(f"{RED}✗ Test suite not found: {script_path}{NC}")
            results.append((suite_name, False))
    
    end_time = datetime.now()
    
    # Generate report
    success = generate_report(results, start_time, end_time)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
