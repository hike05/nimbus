#!/usr/bin/env python3
"""
Test script for client configuration generation.
Tests all protocol configurations and QR code generation.
"""

import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'admin-panel'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'admin-panel' / 'core'))

from interfaces import User
from config_generator import ConfigGenerator
from qr_generator import QRCodeGenerator

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log(message):
    print(f"{BLUE}[INFO]{RESET} {message}")

def success(message):
    print(f"{GREEN}[SUCCESS]{RESET} {message}")

def error(message):
    print(f"{RED}[ERROR]{RESET} {message}")

def warn(message):
    print(f"{YELLOW}[WARN]{RESET} {message}")

def test_config_generation():
    """Test configuration generation for all protocols."""
    log("Testing client configuration generation...")
    
    # Create test user
    test_user = User(
        username="testuser",
        id="12345678-1234-1234-1234-123456789012",
        xray_uuid="87654321-4321-4321-4321-210987654321",
        wireguard_private_key="cGVlcnByaXZhdGVrZXkxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMg==",
        wireguard_public_key="cHVibGlja2V5MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg=",
        trojan_password="trojan_password_1234567890",
        shadowtls_password="shadowtls_pass_123",
        hysteria2_password="hysteria2_pass_456",
        tuic_uuid="11111111-2222-3333-4444-555555555555",
        tuic_password="tuic_password_789",
        created_at="2025-01-01T00:00:00Z",
        is_active=True
    )
    
    # Initialize generator
    config_dir = "/tmp/test-configs"
    os.makedirs(config_dir, exist_ok=True)
    
    generator = ConfigGenerator(config_dir, "test-domain.com")
    
    # Generate configurations
    log("Generating client configurations...")
    configs = generator.generate_client_configs("testuser", test_user)
    
    # Check each protocol
    protocols = {
        'xray_xtls_link': 'Xray XTLS-Vision Link',
        'xray_xtls_json': 'Xray XTLS-Vision JSON',
        'xray_ws_link': 'Xray WebSocket Link',
        'xray_ws_json': 'Xray WebSocket JSON',
        'trojan_link': 'Trojan-Go Link',
        'trojan_json': 'Trojan-Go JSON',
        'shadowtls_json': 'ShadowTLS v3 JSON',
        'hysteria2_link': 'Hysteria2 Link',
        'hysteria2_json': 'Hysteria2 JSON',
        'tuic_json': 'TUIC v5 JSON',
        'wireguard_conf': 'WireGuard Native Config',
        'wireguard_obfs_conf': 'WireGuard WebSocket Config'
    }
    
    print("\n" + "="*60)
    print("Configuration Generation Results:")
    print("="*60)
    
    for key, name in protocols.items():
        if key in configs and configs[key]:
            success(f"✓ {name}")
            if 'link' in key:
                print(f"  {configs[key][:80]}...")
        else:
            warn(f"✗ {name} - Not generated")
    
    return configs

def test_qr_generation():
    """Test QR code generation."""
    log("\nTesting QR code generation...")
    
    # Create test user
    test_user = User(
        username="testuser",
        id="12345678-1234-1234-1234-123456789012",
        xray_uuid="87654321-4321-4321-4321-210987654321",
        wireguard_private_key="cGVlcnByaXZhdGVrZXkxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMg==",
        wireguard_public_key="cHVibGlja2V5MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg=",
        trojan_password="trojan_password_1234567890",
        shadowtls_password="shadowtls_pass_123",
        hysteria2_password="hysteria2_pass_456",
        tuic_uuid="11111111-2222-3333-4444-555555555555",
        tuic_password="tuic_password_789",
        created_at="2025-01-01T00:00:00Z",
        is_active=True
    )
    
    config_dir = "/tmp/test-configs"
    qr_generator = QRCodeGenerator(config_dir, "test-domain.com")
    
    # Generate QR codes
    log("Generating QR codes...")
    qr_codes = qr_generator.generate_all_qr_codes("testuser", test_user)
    
    print("\n" + "="*60)
    print("QR Code Generation Results:")
    print("="*60)
    
    qr_types = {
        'xray_xtls': 'Xray XTLS-Vision',
        'xray_ws': 'Xray WebSocket',
        'trojan': 'Trojan-Go',
        'hysteria2': 'Hysteria2',
        'wireguard': 'WireGuard',
        'shadowtls': 'ShadowTLS v3',
        'tuic': 'TUIC v5'
    }
    
    for key, name in qr_types.items():
        if key in qr_codes and qr_codes[key]:
            success(f"✓ {name} QR Code (base64 length: {len(qr_codes[key])})")
        else:
            warn(f"✗ {name} QR Code - Not generated")
    
    # Test saving QR codes
    output_dir = "/tmp/test-qr-codes"
    os.makedirs(output_dir, exist_ok=True)
    
    log(f"\nSaving QR codes to {output_dir}...")
    saved_files = qr_generator.save_qr_codes("testuser", test_user, output_dir)
    
    print("\n" + "="*60)
    print("Saved QR Code Files:")
    print("="*60)
    
    for key, filepath in saved_files.items():
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            success(f"✓ {filepath} ({size} bytes)")
        else:
            error(f"✗ {filepath} - File not found")
    
    return qr_codes

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Client Configuration Generation Test Suite")
    print("="*60 + "\n")
    
    try:
        # Test configuration generation
        configs = test_config_generation()
        
        # Test QR code generation
        qr_codes = test_qr_generation()
        
        print("\n" + "="*60)
        success("All tests completed successfully!")
        print("="*60 + "\n")
        
        return 0
    except Exception as e:
        error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
