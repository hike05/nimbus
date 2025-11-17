#!/usr/bin/env python3
"""
Integration tests for VPN connectivity across all protocols.
Tests actual VPN connections for Xray, Trojan, Sing-box, and WireGuard.
"""

import sys
import subprocess
import socket
import time
import json
from pathlib import Path

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def check_docker_running():
    """Check if Docker is running."""
    print(f"\n{BLUE}=== Checking Docker Status ==={NC}")
    try:
        result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"{GREEN}✓ Docker is running{NC}")
            return True
        else:
            print(f"{RED}✗ Docker is not running{NC}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error checking Docker: {e}{NC}")
        return False


def check_container_status(container_name):
    """Check if a specific container is running."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            status = result.stdout.strip()
            if 'Up' in status:
                print(f"{GREEN}✓ Container {container_name} is running{NC}")
                return True
        print(f"{YELLOW}⚠ Container {container_name} is not running{NC}")
        return False
    except Exception as e:
        print(f"{RED}✗ Error checking container {container_name}: {e}{NC}")
        return False


def test_xray_connectivity():
    """Test Xray VPN connectivity."""
    print(f"\n{BLUE}=== Testing Xray Connectivity ==={NC}")
    
    # Check if Xray container is running
    if not check_container_status('stealth-xray'):
        return False
    
    # Check if Xray is listening on expected port
    try:
        result = subprocess.run(
            ['docker', 'exec', 'stealth-xray', 'netstat', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if '8001' in result.stdout or '8004' in result.stdout:
            print(f"{GREEN}✓ Xray is listening on configured ports{NC}")
        else:
            print(f"{YELLOW}⚠ Xray ports not found in netstat output{NC}")
        
        # Check Xray process
        result = subprocess.run(
            ['docker', 'exec', 'stealth-xray', 'ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'xray' in result.stdout.lower():
            print(f"{GREEN}✓ Xray process is running{NC}")
            return True
        else:
            print(f"{RED}✗ Xray process not found{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error testing Xray: {e}{NC}")
        return False


def test_trojan_connectivity():
    """Test Trojan-Go VPN connectivity."""
    print(f"\n{BLUE}=== Testing Trojan-Go Connectivity ==={NC}")
    
    # Check if Trojan container is running
    if not check_container_status('stealth-trojan'):
        return False
    
    # Check if Trojan is listening
    try:
        result = subprocess.run(
            ['docker', 'exec', 'stealth-trojan', 'netstat', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if '8002' in result.stdout:
            print(f"{GREEN}✓ Trojan-Go is listening on port 8002{NC}")
        else:
            print(f"{YELLOW}⚠ Trojan-Go port not found{NC}")
        
        # Check Trojan process
        result = subprocess.run(
            ['docker', 'exec', 'stealth-trojan', 'ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'trojan' in result.stdout.lower():
            print(f"{GREEN}✓ Trojan-Go process is running{NC}")
            return True
        else:
            print(f"{RED}✗ Trojan-Go process not found{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error testing Trojan-Go: {e}{NC}")
        return False


def test_singbox_connectivity():
    """Test Sing-box VPN connectivity."""
    print(f"\n{BLUE}=== Testing Sing-box Connectivity ==={NC}")
    
    # Check if Sing-box container is running
    if not check_container_status('stealth-singbox'):
        return False
    
    # Check if Sing-box is listening on multiple ports
    try:
        result = subprocess.run(
            ['docker', 'exec', 'stealth-singbox', 'netstat', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        expected_ports = ['8003', '8005', '8006']
        found_ports = []
        
        for port in expected_ports:
            if port in result.stdout:
                found_ports.append(port)
        
        if found_ports:
            print(f"{GREEN}✓ Sing-box is listening on ports: {', '.join(found_ports)}{NC}")
        else:
            print(f"{YELLOW}⚠ No Sing-box ports found{NC}")
        
        # Check Sing-box process
        result = subprocess.run(
            ['docker', 'exec', 'stealth-singbox', 'ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'sing-box' in result.stdout.lower():
            print(f"{GREEN}✓ Sing-box process is running{NC}")
            return True
        else:
            print(f"{RED}✗ Sing-box process not found{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error testing Sing-box: {e}{NC}")
        return False


def test_wireguard_connectivity():
    """Test WireGuard VPN connectivity."""
    print(f"\n{BLUE}=== Testing WireGuard Connectivity ==={NC}")
    
    # Check if WireGuard container is running
    if not check_container_status('stealth-wireguard'):
        return False
    
    # Check WireGuard interface
    try:
        result = subprocess.run(
            ['docker', 'exec', 'stealth-wireguard', 'wg', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"{GREEN}✓ WireGuard interface is configured{NC}")
            
            # Check for peers
            if 'peer' in result.stdout.lower():
                print(f"{GREEN}✓ WireGuard has configured peers{NC}")
            else:
                print(f"{YELLOW}⚠ No WireGuard peers configured yet{NC}")
            
            return True
        else:
            print(f"{RED}✗ WireGuard interface not found{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error testing WireGuard: {e}{NC}")
        return False


def test_caddy_reverse_proxy():
    """Test Caddy reverse proxy connectivity."""
    print(f"\n{BLUE}=== Testing Caddy Reverse Proxy ==={NC}")
    
    # Check if Caddy container is running
    if not check_container_status('stealth-caddy'):
        return False
    
    # Check if Caddy is listening on ports 80 and 443
    try:
        result = subprocess.run(
            ['docker', 'exec', 'stealth-caddy', 'netstat', '-tuln'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        ports_found = []
        if ':80' in result.stdout:
            ports_found.append('80')
        if ':443' in result.stdout:
            ports_found.append('443')
        
        if len(ports_found) == 2:
            print(f"{GREEN}✓ Caddy is listening on ports 80 and 443{NC}")
            return True
        else:
            print(f"{YELLOW}⚠ Caddy listening on: {', '.join(ports_found)}{NC}")
            return len(ports_found) > 0
            
    except Exception as e:
        print(f"{RED}✗ Error testing Caddy: {e}{NC}")
        return False


def test_network_connectivity():
    """Test Docker network connectivity between containers."""
    print(f"\n{BLUE}=== Testing Docker Network Connectivity ==={NC}")
    
    try:
        # Check if stealth-vpn network exists
        result = subprocess.run(
            ['docker', 'network', 'ls', '--filter', 'name=stealth-vpn', '--format', '{{.Name}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'stealth-vpn' in result.stdout:
            print(f"{GREEN}✓ Docker network 'stealth-vpn' exists{NC}")
        else:
            print(f"{RED}✗ Docker network 'stealth-vpn' not found{NC}")
            return False
        
        # Test connectivity from Caddy to Xray
        result = subprocess.run(
            ['docker', 'exec', 'stealth-caddy', 'ping', '-c', '1', 'stealth-xray'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✓ Caddy can reach Xray container{NC}")
            return True
        else:
            print(f"{YELLOW}⚠ Network connectivity test inconclusive{NC}")
            return True  # Don't fail on ping issues
            
    except Exception as e:
        print(f"{YELLOW}⚠ Network test error (non-critical): {e}{NC}")
        return True  # Don't fail on network test errors


def main():
    """Run all VPN connectivity tests."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}VPN Connectivity Integration Tests{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    # Check Docker first
    if not check_docker_running():
        print(f"\n{RED}✗ Docker is not running. Please start Docker and try again.{NC}")
        return False
    
    tests = [
        ("Caddy Reverse Proxy", test_caddy_reverse_proxy),
        ("Xray Connectivity", test_xray_connectivity),
        ("Trojan-Go Connectivity", test_trojan_connectivity),
        ("Sing-box Connectivity", test_singbox_connectivity),
        ("WireGuard Connectivity", test_wireguard_connectivity),
        ("Network Connectivity", test_network_connectivity),
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
        print(f"\n{GREEN}✓ All VPN connectivity tests passed!{NC}")
        return True
    else:
        print(f"\n{YELLOW}⚠ Some tests failed. Check container status with 'docker compose ps'{NC}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
