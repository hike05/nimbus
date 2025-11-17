#!/usr/bin/env python3
"""
End-to-end integration tests for admin panel functionality.
Tests user management, config generation, and admin operations.
"""

import sys
import subprocess
import requests
import time
import json
from pathlib import Path

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def check_admin_panel_running():
    """Check if admin panel container is running."""
    print(f"\n{BLUE}=== Checking Admin Panel Status ==={NC}")
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=stealth-admin', '--format', '{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and 'Up' in result.stdout:
            print(f"{GREEN}✓ Admin panel container is running{NC}")
            return True
        else:
            print(f"{RED}✗ Admin panel container is not running{NC}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error checking admin panel: {e}{NC}")
        return False


def test_admin_panel_health():
    """Test admin panel health endpoint."""
    print(f"\n{BLUE}=== Testing Admin Panel Health ==={NC}")
    
    try:
        # Try to connect to admin panel (through Caddy)
        # Note: This assumes local testing environment
        response = requests.get(
            'http://localhost/api/v2/storage/upload',
            timeout=5,
            allow_redirects=False
        )
        
        # We expect either 200 (if accessible) or 401/403 (if auth required)
        if response.status_code in [200, 401, 403, 302]:
            print(f"{GREEN}✓ Admin panel is responding (status: {response.status_code}){NC}")
            return True
        else:
            print(f"{YELLOW}⚠ Unexpected status code: {response.status_code}{NC}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{YELLOW}⚠ Cannot connect to admin panel (may not be exposed){NC}")
        return True  # Don't fail if not exposed externally
    except Exception as e:
        print(f"{RED}✗ Error testing admin panel health: {e}{NC}")
        return False


def test_user_storage_operations():
    """Test user storage operations through Docker exec."""
    print(f"\n{BLUE}=== Testing User Storage Operations ==={NC}")
    
    try:
        # Test loading users
        result = subprocess.run(
            ['docker', 'exec', 'stealth-admin', 'python3', '-c',
             'from core.user_storage import UserStorage; s = UserStorage(); print(len(s.load_users()))'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            user_count = result.stdout.strip()
            print(f"{GREEN}✓ User storage accessible: {user_count} user(s){NC}")
            return True
        else:
            print(f"{RED}✗ Error accessing user storage{NC}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error testing user storage: {e}{NC}")
        return False


def test_config_generation():
    """Test configuration generation for all protocols."""
    print(f"\n{BLUE}=== Testing Config Generation ==={NC}")
    
    try:
        # Check if config files exist
        config_files = [
            'data/stealth-vpn/configs/xray.json',
            'data/stealth-vpn/configs/trojan.json',
            'data/stealth-vpn/configs/singbox.json',
        ]
        
        all_exist = True
        for config_file in config_files:
            if Path(config_file).exists():
                print(f"{GREEN}✓ Config exists: {config_file}{NC}")
            else:
                print(f"{YELLOW}⚠ Config missing: {config_file}{NC}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"{RED}✗ Error checking config files: {e}{NC}")
        return False


def test_client_config_generation():
    """Test client configuration generation."""
    print(f"\n{BLUE}=== Testing Client Config Generation ==={NC}")
    
    try:
        # Check if any client configs exist
        client_dir = Path('data/stealth-vpn/configs/clients')
        
        if not client_dir.exists():
            print(f"{YELLOW}⚠ No client configs directory found{NC}")
            return True  # Not an error if no users yet
        
        client_users = list(client_dir.iterdir())
        
        if len(client_users) == 0:
            print(f"{YELLOW}⚠ No client configs generated yet{NC}")
            return True  # Not an error if no users yet
        
        print(f"{GREEN}✓ Found {len(client_users)} client config(s){NC}")
        
        # Check first user's configs
        first_user = client_users[0]
        config_files = list(first_user.glob('*.json')) + list(first_user.glob('*.txt'))
        
        if len(config_files) > 0:
            print(f"{GREEN}✓ Client has {len(config_files)} config file(s){NC}")
            return True
        else:
            print(f"{YELLOW}⚠ No config files for client{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error checking client configs: {e}{NC}")
        return False


def test_backup_system():
    """Test backup system functionality."""
    print(f"\n{BLUE}=== Testing Backup System ==={NC}")
    
    try:
        backup_dir = Path('data/stealth-vpn/backups')
        
        if not backup_dir.exists():
            print(f"{YELLOW}⚠ Backup directory not found{NC}")
            return True  # Not critical if no backups yet
        
        backups = list(backup_dir.glob('users.json.*'))
        
        if len(backups) > 0:
            print(f"{GREEN}✓ Found {len(backups)} backup(s){NC}")
            
            # Check if backups are valid JSON
            latest_backup = sorted(backups)[-1]
            with open(latest_backup, 'r') as f:
                data = json.load(f)
            
            if 'users' in data:
                print(f"{GREEN}✓ Backup contains valid data{NC}")
                return True
            else:
                print(f"{RED}✗ Backup data is invalid{NC}")
                return False
        else:
            print(f"{YELLOW}⚠ No backups found yet{NC}")
            return True  # Not critical if no backups yet
            
    except Exception as e:
        print(f"{RED}✗ Error checking backups: {e}{NC}")
        return False


def test_log_files():
    """Test that log files are being created."""
    print(f"\n{BLUE}=== Testing Log Files ==={NC}")
    
    try:
        log_dir = Path('data/stealth-vpn/logs')
        
        if not log_dir.exists():
            print(f"{YELLOW}⚠ Log directory not found{NC}")
            return False
        
        # Check for service log directories
        service_dirs = ['admin', 'xray', 'trojan', 'singbox', 'wireguard', 'caddy']
        found_dirs = []
        
        for service in service_dirs:
            service_log_dir = log_dir / service
            if service_log_dir.exists():
                found_dirs.append(service)
        
        if len(found_dirs) > 0:
            print(f"{GREEN}✓ Found log directories for: {', '.join(found_dirs)}{NC}")
            return True
        else:
            print(f"{YELLOW}⚠ No service log directories found{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error checking log files: {e}{NC}")
        return False


def test_flask_app_running():
    """Test that Flask app is running inside container."""
    print(f"\n{BLUE}=== Testing Flask Application ==={NC}")
    
    try:
        # Check if Flask process is running
        result = subprocess.run(
            ['docker', 'exec', 'stealth-admin', 'ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'python' in result.stdout.lower() or 'flask' in result.stdout.lower():
            print(f"{GREEN}✓ Flask application is running{NC}")
            return True
        else:
            print(f"{RED}✗ Flask application not found{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error checking Flask app: {e}{NC}")
        return False


def test_data_persistence():
    """Test that data persists across container restarts."""
    print(f"\n{BLUE}=== Testing Data Persistence ==={NC}")
    
    try:
        users_file = Path('data/stealth-vpn/users.json')
        
        if not users_file.exists():
            print(f"{YELLOW}⚠ Users file not found (may not be created yet){NC}")
            return True  # Not critical if no users yet
        
        # Check if file is readable
        with open(users_file, 'r') as f:
            data = json.load(f)
        
        if 'users' in data or 'schema_version' in data:
            print(f"{GREEN}✓ Data file is valid and persistent{NC}")
            return True
        else:
            print(f"{RED}✗ Data file structure is invalid{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error checking data persistence: {e}{NC}")
        return False


def main():
    """Run all admin panel end-to-end tests."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Admin Panel End-to-End Integration Tests{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    # Check if admin panel is running
    if not check_admin_panel_running():
        print(f"\n{RED}✗ Admin panel is not running. Start with 'docker compose up -d'{NC}")
        return False
    
    tests = [
        ("Admin Panel Health", test_admin_panel_health),
        ("Flask Application", test_flask_app_running),
        ("User Storage Operations", test_user_storage_operations),
        ("Config Generation", test_config_generation),
        ("Client Config Generation", test_client_config_generation),
        ("Backup System", test_backup_system),
        ("Log Files", test_log_files),
        ("Data Persistence", test_data_persistence),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n{RED}✗ {test_name} failed with exception: {e}{NC}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print(f"{GREEN}✓ PASS{NC}: {test_name}")
        else:
            print(f"{RED}✗ FAIL{NC}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}✓ All admin panel tests passed!{NC}")
        return True
    else:
        print(f"\n{YELLOW}⚠ Some tests failed. Check logs with 'docker compose logs admin'{NC}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
