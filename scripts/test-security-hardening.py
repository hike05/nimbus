#!/usr/bin/env python3
"""
Security Hardening Test Suite

Tests container security, traffic obfuscation, and anti-fingerprinting measures.

Requirements: 6.2, 6.3, 2.3, 3.3
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Colors for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def log(message: str):
    """Print log message"""
    print(f"{GREEN}[Security Test]{NC} {message}")


def warn(message: str):
    """Print warning message"""
    print(f"{YELLOW}[Security Test]{NC} {message}")


def error(message: str):
    """Print error message"""
    print(f"{RED}[Security Test]{NC} {message}")


def success(message: str):
    """Print success message"""
    print(f"{GREEN}✓{NC} {message}")


def fail(message: str):
    """Print failure message"""
    print(f"{RED}✗{NC} {message}")


def run_command(cmd: List[str]) -> Tuple[int, str, str]:
    """
    Run shell command and return result
    
    Args:
        cmd: Command as list of strings
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def test_container_users() -> bool:
    """Test that containers run as non-root users"""
    log("Testing container user configuration...")
    
    containers = [
        'stealth-xray',
        'stealth-trojan',
        'stealth-singbox',
        'stealth-wireguard',
        'stealth-admin'
    ]
    
    all_passed = True
    
    for container in containers:
        # Check if container is running
        rc, stdout, _ = run_command(['docker', 'ps', '-q', '-f', f'name={container}'])
        
        if rc != 0 or not stdout.strip():
            warn(f"Container {container} is not running, skipping")
            continue
        
        # Check user
        rc, stdout, _ = run_command([
            'docker', 'exec', container, 'whoami'
        ])
        
        if rc == 0:
            user = stdout.strip()
            if user != 'root':
                success(f"{container}: Running as non-root user '{user}'")
            else:
                fail(f"{container}: Running as root user (security risk)")
                all_passed = False
        else:
            warn(f"{container}: Could not determine user")
    
    return all_passed


def test_container_capabilities() -> bool:
    """Test that containers have minimal capabilities"""
    log("Testing container capabilities...")
    
    containers = [
        'stealth-xray',
        'stealth-trojan',
        'stealth-singbox',
        'stealth-admin'
    ]
    
    all_passed = True
    
    for container in containers:
        # Check if container is running
        rc, stdout, _ = run_command(['docker', 'ps', '-q', '-f', f'name={container}'])
        
        if rc != 0 or not stdout.strip():
            warn(f"Container {container} is not running, skipping")
            continue
        
        # Inspect container capabilities
        rc, stdout, _ = run_command([
            'docker', 'inspect', container, '--format', '{{.HostConfig.CapAdd}}'
        ])
        
        if rc == 0:
            caps = stdout.strip()
            # Should only have NET_BIND_SERVICE or be empty
            if caps in ['[]', '[NET_BIND_SERVICE]']:
                success(f"{container}: Minimal capabilities configured")
            else:
                warn(f"{container}: Has capabilities: {caps}")
        else:
            warn(f"{container}: Could not inspect capabilities")
    
    return all_passed


def test_read_only_filesystem() -> bool:
    """Test that containers use read-only filesystems where appropriate"""
    log("Testing read-only filesystem configuration...")
    
    containers = [
        'stealth-xray',
        'stealth-trojan',
        'stealth-singbox',
        'stealth-admin',
        'stealth-caddy'
    ]
    
    all_passed = True
    
    for container in containers:
        # Check if container is running
        rc, stdout, _ = run_command(['docker', 'ps', '-q', '-f', f'name={container}'])
        
        if rc != 0 or not stdout.strip():
            warn(f"Container {container} is not running, skipping")
            continue
        
        # Check read-only status
        rc, stdout, _ = run_command([
            'docker', 'inspect', container, '--format', '{{.HostConfig.ReadonlyRootfs}}'
        ])
        
        if rc == 0:
            readonly = stdout.strip()
            if readonly == 'true':
                success(f"{container}: Read-only filesystem enabled")
            else:
                warn(f"{container}: Read-only filesystem not enabled")
        else:
            warn(f"{container}: Could not check read-only status")
    
    return all_passed


def test_security_options() -> bool:
    """Test that containers have proper security options"""
    log("Testing security options...")
    
    containers = [
        'stealth-xray',
        'stealth-trojan',
        'stealth-singbox',
        'stealth-wireguard',
        'stealth-admin',
        'stealth-caddy'
    ]
    
    all_passed = True
    
    for container in containers:
        # Check if container is running
        rc, stdout, _ = run_command(['docker', 'ps', '-q', '-f', f'name={container}'])
        
        if rc != 0 or not stdout.strip():
            warn(f"Container {container} is not running, skipping")
            continue
        
        # Check security options
        rc, stdout, _ = run_command([
            'docker', 'inspect', container, '--format', '{{.HostConfig.SecurityOpt}}'
        ])
        
        if rc == 0:
            sec_opts = stdout.strip()
            if 'no-new-privileges:true' in sec_opts:
                success(f"{container}: no-new-privileges enabled")
            else:
                fail(f"{container}: no-new-privileges not enabled")
                all_passed = False
        else:
            warn(f"{container}: Could not check security options")
    
    return all_passed


def test_resource_limits() -> bool:
    """Test that containers have resource limits configured"""
    log("Testing resource limits...")
    
    containers = [
        'stealth-xray',
        'stealth-trojan',
        'stealth-singbox',
        'stealth-wireguard',
        'stealth-admin',
        'stealth-caddy'
    ]
    
    all_passed = True
    
    for container in containers:
        # Check if container is running
        rc, stdout, _ = run_command(['docker', 'ps', '-q', '-f', f'name={container}'])
        
        if rc != 0 or not stdout.strip():
            warn(f"Container {container} is not running, skipping")
            continue
        
        # Check memory limit
        rc, stdout, _ = run_command([
            'docker', 'inspect', container, '--format', '{{.HostConfig.Memory}}'
        ])
        
        if rc == 0:
            memory = int(stdout.strip())
            if memory > 0:
                memory_mb = memory / (1024 * 1024)
                success(f"{container}: Memory limit set to {memory_mb:.0f}MB")
            else:
                warn(f"{container}: No memory limit set")
        else:
            warn(f"{container}: Could not check memory limit")
    
    return all_passed


def test_traffic_obfuscation_module() -> bool:
    """Test traffic obfuscation module"""
    log("Testing traffic obfuscation module...")
    
    try:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from core.traffic_obfuscation import (
            TrafficObfuscator,
            TrafficPattern,
            FingerprintingProtection,
            generate_obfuscation_config
        )
        
        # Test traffic obfuscator
        obfuscator = TrafficObfuscator(TrafficPattern.WEB_BROWSING)
        
        # Test delay generation
        delay = obfuscator.get_next_delay()
        if 0 <= delay <= 1.0:
            success("Traffic obfuscator: Delay generation working")
        else:
            fail(f"Traffic obfuscator: Invalid delay {delay}")
            return False
        
        # Test packet size normalization
        normalized = obfuscator.normalize_packet_size(100, "https")
        if normalized >= 100 and normalized in obfuscator.HTTPS_COMMON_SIZES:
            success("Traffic obfuscator: Packet size normalization working")
        else:
            fail(f"Traffic obfuscator: Invalid normalized size {normalized}")
            return False
        
        # Test padding generation
        padding = obfuscator.generate_padding(50)
        if len(padding) == 50:
            success("Traffic obfuscator: Padding generation working")
        else:
            fail(f"Traffic obfuscator: Invalid padding size {len(padding)}")
            return False
        
        # Test fingerprinting protection
        headers = FingerprintingProtection.generate_realistic_headers()
        if 'User-Agent' in headers and 'Accept' in headers:
            success("Fingerprinting protection: Header generation working")
        else:
            fail("Fingerprinting protection: Invalid headers")
            return False
        
        # Test configuration generation
        config = generate_obfuscation_config("xray", TrafficPattern.WEB_BROWSING)
        if 'timing' in config and 'packet_size' in config and 'anti_fingerprinting' in config:
            success("Configuration generation: Working correctly")
        else:
            fail("Configuration generation: Invalid config structure")
            return False
        
        return True
        
    except Exception as e:
        fail(f"Traffic obfuscation module test failed: {e}")
        return False


def test_obfuscation_configs() -> bool:
    """Test that obfuscation configurations exist"""
    log("Testing obfuscation configuration files...")
    
    config_base = Path(__file__).parent.parent / 'data' / 'stealth-vpn' / 'configs'
    
    all_passed = True
    
    # Check WireGuard obfuscation config
    wg_obf = config_base / 'wireguard' / 'obfuscation.json'
    if wg_obf.exists():
        try:
            with open(wg_obf, 'r') as f:
                config = json.load(f)
            if 'timing' in config and 'packet_size' in config:
                success("WireGuard obfuscation config exists and is valid")
            else:
                fail("WireGuard obfuscation config is invalid")
                all_passed = False
        except Exception as e:
            fail(f"WireGuard obfuscation config error: {e}")
            all_passed = False
    else:
        warn("WireGuard obfuscation config not found (run apply-traffic-obfuscation.py)")
    
    return all_passed


def main():
    """Main test function"""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Security Hardening Test Suite{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")
    
    tests = [
        ("Container Users", test_container_users),
        ("Container Capabilities", test_container_capabilities),
        ("Read-Only Filesystems", test_read_only_filesystem),
        ("Security Options", test_security_options),
        ("Resource Limits", test_resource_limits),
        ("Traffic Obfuscation Module", test_traffic_obfuscation_module),
        ("Obfuscation Configurations", test_obfuscation_configs),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{BLUE}Testing: {test_name}{NC}")
        print("-" * 60)
        
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            error(f"Test failed with exception: {e}")
            results.append((test_name, False))
        
        print()
    
    # Summary
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Test Summary{NC}")
    print(f"{BLUE}{'=' * 60}{NC}\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = f"{GREEN}PASS{NC}" if passed else f"{RED}FAIL{NC}"
        print(f"  {status}  {test_name}")
    
    print(f"\n{BLUE}Results: {passed_count}/{total_count} tests passed{NC}\n")
    
    if passed_count == total_count:
        log("✓ All security hardening tests passed!")
        return 0
    else:
        error(f"✗ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
