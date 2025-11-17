"""
QR code generator for VPN client configurations.
Generates QR codes for mobile client apps.
"""

import qrcode
import io
import base64
from typing import Dict, Optional
import sys

sys.path.insert(0, '/app/core')
from interfaces import User
from config_generator import ConfigGenerator


class QRCodeGenerator:
    """Generates QR codes for VPN configurations."""
    
    def __init__(self, config_dir: str = "/data/stealth-vpn/configs", domain: str = "your-domain.com"):
        self.config_generator = ConfigGenerator(config_dir, domain)
    
    def generate_qr_code(self, data: str, format: str = 'PNG') -> bytes:
        """Generate QR code image from data string."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format=format)
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
    
    def generate_qr_code_base64(self, data: str) -> str:
        """Generate QR code as base64 encoded string for HTML embedding."""
        qr_bytes = self.generate_qr_code(data)
        return base64.b64encode(qr_bytes).decode('utf-8')
    
    def generate_all_qr_codes(self, username: str, user: User) -> Dict[str, str]:
        """Generate QR codes for all supported protocols."""
        qr_codes = {}
        
        # Generate configuration links
        configs = self.config_generator.generate_client_configs(username, user)
        
        # Xray XTLS-Vision
        if 'xray_xtls_link' in configs:
            qr_codes['xray_xtls'] = self.generate_qr_code_base64(configs['xray_xtls_link'])
        
        # Xray WebSocket
        if 'xray_ws_link' in configs:
            qr_codes['xray_ws'] = self.generate_qr_code_base64(configs['xray_ws_link'])
        
        # Trojan
        if 'trojan_link' in configs:
            qr_codes['trojan'] = self.generate_qr_code_base64(configs['trojan_link'])
        
        # Hysteria2
        if 'hysteria2_link' in configs:
            qr_codes['hysteria2'] = self.generate_qr_code_base64(configs['hysteria2_link'])
        
        # WireGuard (native config)
        if 'wireguard_conf' in configs:
            qr_codes['wireguard'] = self.generate_qr_code_base64(configs['wireguard_conf'])
        
        # Sing-box JSON configs (for mobile apps that support JSON import)
        if 'shadowtls_json' in configs:
            qr_codes['shadowtls'] = self.generate_qr_code_base64(configs['shadowtls_json'])
        
        if 'hysteria2_json' in configs:
            qr_codes['hysteria2_json'] = self.generate_qr_code_base64(configs['hysteria2_json'])
        
        if 'tuic_json' in configs:
            qr_codes['tuic'] = self.generate_qr_code_base64(configs['tuic_json'])
        
        return qr_codes
    
    def save_qr_codes(self, username: str, user: User, output_dir: str) -> Dict[str, str]:
        """Save QR codes as PNG files."""
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        configs = self.config_generator.generate_client_configs(username, user)
        
        # Save each QR code
        qr_mappings = {
            'xray_xtls_link': 'xray-xtls-qr.png',
            'xray_ws_link': 'xray-ws-qr.png',
            'trojan_link': 'trojan-qr.png',
            'hysteria2_link': 'hysteria2-qr.png',
            'wireguard_conf': 'wireguard-qr.png',
        }
        
        for config_key, filename in qr_mappings.items():
            if config_key in configs:
                qr_bytes = self.generate_qr_code(configs[config_key])
                file_path = output_path / filename
                with open(file_path, 'wb') as f:
                    f.write(qr_bytes)
                saved_files[config_key] = str(file_path)
        
        return saved_files
