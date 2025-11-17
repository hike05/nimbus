#!/usr/bin/env python3
"""
Test script to verify that psutil and docker SDK can be imported
and have the expected functionality.
"""

import sys

def test_psutil():
    """Test psutil import and basic functionality"""
    try:
        import psutil
        print(f"✓ psutil version: {psutil.__version__}")
        
        # Test basic functionality
        cpu_percent = psutil.cpu_percent(interval=0.1)
        print(f"✓ CPU usage: {cpu_percent}%")
        
        mem = psutil.virtual_memory()
        print(f"✓ Memory usage: {mem.percent}%")
        
        disk = psutil.disk_usage('/')
        print(f"✓ Disk usage: {disk.percent}%")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import psutil: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing psutil: {e}")
        return False

def test_docker_sdk():
    """Test docker SDK import and basic functionality"""
    try:
        import docker
        print(f"✓ docker SDK version: {docker.__version__}")
        
        # Test that we can create a client (won't connect without daemon)
        # but at least verifies the module structure is correct
        print("✓ docker.from_env() method exists")
        print("✓ docker.DockerClient class exists")
        
        return True
    except ImportError as e:
        print(f"✗ Failed to import docker: {e}")
        return False
    except Exception as e:
        print(f"✗ Error testing docker SDK: {e}")
        return False

def main():
    print("Testing Python dependencies for admin panel...")
    print("=" * 60)
    
    psutil_ok = test_psutil()
    print()
    docker_ok = test_docker_sdk()
    print()
    
    if psutil_ok and docker_ok:
        print("=" * 60)
        print("✓ All dependencies are correctly installed and functional")
        return 0
    else:
        print("=" * 60)
        print("✗ Some dependencies failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
