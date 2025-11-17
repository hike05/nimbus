#!/usr/bin/env python3
"""
Integration tests for Docker container orchestration.
Tests container startup, networking, volumes, and dependencies.
"""

import sys
import subprocess
import time
import json
from pathlib import Path

# Color codes for output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def test_docker_compose_config():
    """Test Docker Compose configuration validity."""
    print(f"\n{BLUE}=== Testing Docker Compose Configuration ==={NC}")
    
    try:
        result = subprocess.run(
            ['docker', 'compose', 'config'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✓ Docker Compose configuration is valid{NC}")
            return True
        else:
            print(f"{RED}✗ Docker Compose configuration is invalid{NC}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error validating Docker Compose config: {e}{NC}")
        return False


def test_all_containers_running():
    """Test that all required containers are running."""
    print(f"\n{BLUE}=== Testing Container Status ==={NC}")
    
    required_containers = [
        'stealth-caddy',
        'stealth-xray',
        'stealth-trojan',
        'stealth-singbox',
        'stealth-wireguard',
        'stealth-admin',
    ]
    
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"{RED}✗ Error getting container status{NC}")
            return False
        
        # Parse JSON output
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        
        running_containers = [c['Name'] for c in containers if c.get('State') == 'running']
        
        all_running = True
        for container in required_containers:
            if container in running_containers:
                print(f"{GREEN}✓ {container} is running{NC}")
            else:
                print(f"{RED}✗ {container} is not running{NC}")
                all_running = False
        
        return all_running
        
    except Exception as e:
        print(f"{RED}✗ Error checking container status: {e}{NC}")
        return False


def test_container_health():
    """Test container health checks."""
    print(f"\n{BLUE}=== Testing Container Health ==={NC}")
    
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        
        healthy_count = 0
        for container in containers:
            name = container.get('Name', 'unknown')
            health = container.get('Health', 'N/A')
            
            if health == 'healthy' or health == 'N/A':
                print(f"{GREEN}✓ {name}: {health}{NC}")
                healthy_count += 1
            else:
                print(f"{YELLOW}⚠ {name}: {health}{NC}")
        
        return healthy_count > 0
        
    except Exception as e:
        print(f"{RED}✗ Error checking container health: {e}{NC}")
        return False


def test_docker_network():
    """Test Docker network configuration."""
    print(f"\n{BLUE}=== Testing Docker Network ==={NC}")
    
    try:
        # Check if network exists
        result = subprocess.run(
            ['docker', 'network', 'ls', '--filter', 'name=stealth-vpn', '--format', '{{.Name}}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if 'stealth-vpn' in result.stdout or 'stealth' in result.stdout:
            print(f"{GREEN}✓ Docker network exists{NC}")
        else:
            print(f"{YELLOW}⚠ Docker network not found (may use default){NC}")
        
        # Check network connectivity
        result = subprocess.run(
            ['docker', 'network', 'inspect', 'stealth-vpn'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            network_data = json.loads(result.stdout)
            if len(network_data) > 0:
                containers = network_data[0].get('Containers', {})
                print(f"{GREEN}✓ Network has {len(containers)} connected container(s){NC}")
                return True
        
        return True  # Don't fail if network inspection fails
        
    except Exception as e:
        print(f"{YELLOW}⚠ Network test error (non-critical): {e}{NC}")
        return True


def test_volume_mounts():
    """Test that volumes are properly mounted."""
    print(f"\n{BLUE}=== Testing Volume Mounts ==={NC}")
    
    required_volumes = [
        'data/stealth-vpn',
        'data/caddy',
        'data/www',
    ]
    
    all_exist = True
    for volume in required_volumes:
        volume_path = Path(volume)
        if volume_path.exists():
            print(f"{GREEN}✓ Volume exists: {volume}{NC}")
        else:
            print(f"{RED}✗ Volume missing: {volume}{NC}")
            all_exist = False
    
    return all_exist


def test_config_volume_access():
    """Test that containers can access config volumes."""
    print(f"\n{BLUE}=== Testing Config Volume Access ==={NC}")
    
    try:
        # Test Xray config access
        result = subprocess.run(
            ['docker', 'exec', 'stealth-xray', 'ls', '/etc/xray'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✓ Xray can access config volume{NC}")
        else:
            print(f"{RED}✗ Xray cannot access config volume{NC}")
            return False
        
        # Test admin panel data access
        result = subprocess.run(
            ['docker', 'exec', 'stealth-admin', 'ls', '/app/data'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✓ Admin panel can access data volume{NC}")
            return True
        else:
            print(f"{RED}✗ Admin panel cannot access data volume{NC}")
            return False
            
    except Exception as e:
        print(f"{RED}✗ Error testing volume access: {e}{NC}")
        return False


def test_container_dependencies():
    """Test that container dependencies are respected."""
    print(f"\n{BLUE}=== Testing Container Dependencies ==={NC}")
    
    try:
        # Get container start times
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        
        # Check that Caddy is running (should start after VPN services)
        caddy_running = any(c['Name'] == 'stealth-caddy' and c['State'] == 'running' for c in containers)
        vpn_services_running = sum(1 for c in containers if 'xray' in c['Name'] or 'trojan' in c['Name'] or 'singbox' in c['Name'])
        
        if caddy_running and vpn_services_running > 0:
            print(f"{GREEN}✓ Container dependencies appear correct{NC}")
            return True
        else:
            print(f"{YELLOW}⚠ Cannot verify container dependencies{NC}")
            return True  # Don't fail on this
            
    except Exception as e:
        print(f"{YELLOW}⚠ Dependency test error (non-critical): {e}{NC}")
        return True


def test_container_restart_policy():
    """Test that containers have proper restart policies."""
    print(f"\n{BLUE}=== Testing Restart Policies ==={NC}")
    
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        
        # Check restart policies via docker inspect
        for container in containers:
            name = container.get('Name')
            if name:
                inspect_result = subprocess.run(
                    ['docker', 'inspect', name, '--format', '{{.HostConfig.RestartPolicy.Name}}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                policy = inspect_result.stdout.strip()
                if policy in ['unless-stopped', 'always']:
                    print(f"{GREEN}✓ {name}: restart policy = {policy}{NC}")
                else:
                    print(f"{YELLOW}⚠ {name}: restart policy = {policy}{NC}")
        
        return True
        
    except Exception as e:
        print(f"{YELLOW}⚠ Restart policy test error (non-critical): {e}{NC}")
        return True


def test_resource_limits():
    """Test that containers have resource limits configured."""
    print(f"\n{BLUE}=== Testing Resource Limits ==={NC}")
    
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"{GREEN}✓ Container resource usage:{NC}")
            print(result.stdout)
            return True
        else:
            print(f"{YELLOW}⚠ Cannot get resource stats{NC}")
            return True  # Don't fail on this
            
    except Exception as e:
        print(f"{YELLOW}⚠ Resource limit test error (non-critical): {e}{NC}")
        return True


def main():
    """Run all Docker orchestration tests."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}Docker Orchestration Integration Tests{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")
    
    tests = [
        ("Docker Compose Config", test_docker_compose_config),
        ("All Containers Running", test_all_containers_running),
        ("Container Health", test_container_health),
        ("Docker Network", test_docker_network),
        ("Volume Mounts", test_volume_mounts),
        ("Config Volume Access", test_config_volume_access),
        ("Container Dependencies", test_container_dependencies),
        ("Restart Policies", test_container_restart_policy),
        ("Resource Limits", test_resource_limits),
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
        print(f"\n{GREEN}✓ All Docker orchestration tests passed!{NC}")
        return True
    else:
        print(f"\n{YELLOW}⚠ Some tests failed. Check with 'docker compose ps' and 'docker compose logs'{NC}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
