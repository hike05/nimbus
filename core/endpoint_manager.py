"""
Endpoint obfuscation management module
Provides utilities for generating, rotating, and managing obfuscated endpoints
"""

import json
import secrets
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class EndpointConfig:
    """Configuration for an obfuscated endpoint"""
    service_name: str
    path: str
    description: str
    created_at: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class EndpointManager:
    """Manages obfuscated endpoints for VPN services"""
    
    def __init__(self, config_path: str = 'data/stealth-vpn/endpoints.json'):
        """
        Initialize endpoint manager
        
        Args:
            config_path: Path to endpoints configuration file
        """
        self.config_path = Path(config_path)
        self.backup_dir = self.config_path.parent / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_js_path(self) -> str:
        """Generate realistic JavaScript file path"""
        libraries = ['jquery', 'bootstrap', 'analytics', 'tracking', 'metrics', 'stats', 'lodash', 'moment']
        versions = [f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}" for _ in range(3)]
        suffixes = ['min.js', 'bundle.js', 'prod.js', 'chunk.js']
        
        lib = random.choice(libraries)
        version = random.choice(versions)
        suffix = random.choice(suffixes)
        
        paths = [
            f"/assets/js/{lib}-{version}.{suffix}",
            f"/cdn/libs/{lib}/{version}/{lib}.{suffix}",
            f"/static/js/{lib}-{secrets.token_hex(4)}.{suffix}",
            f"/js/vendor/{lib}.{suffix}",
            f"/public/assets/{lib}-{version}.{suffix}"
        ]
        
        return random.choice(paths)
    
    def generate_font_path(self) -> str:
        """Generate realistic font file path"""
        fonts = ['roboto', 'opensans', 'lato', 'montserrat', 'poppins', 'nunito', 'inter', 'raleway']
        weights = ['regular', 'bold', 'light', 'medium', 'semibold', 'thin']
        
        font = random.choice(fonts)
        weight = random.choice(weights)
        
        paths = [
            f"/static/fonts/woff2/{font}-{weight}.woff2",
            f"/assets/fonts/{font}/{font}-{weight}.woff2",
            f"/fonts/{font}-{weight}-{secrets.token_hex(4)}.woff2",
            f"/public/fonts/woff2/{font}.woff2",
            f"/cdn/fonts/{font}/{weight}.woff2"
        ]
        
        return random.choice(paths)
    
    def generate_api_path(self) -> str:
        """Generate realistic API path"""
        versions = ['v1', 'v2', 'v3']
        services = ['storage', 'files', 'cloud', 'sync', 'backup', 'media', 'data']
        actions = ['upload', 'download', 'sync', 'metadata', 'thumbnail', 'preview', 'process']
        
        version = random.choice(versions)
        service = random.choice(services)
        action = random.choice(actions)
        
        paths = [
            f"/api/{version}/{service}/{action}",
            f"/api/{version}/{service}/batch/{action}",
            f"/rest/{version}/{service}/{action}",
            f"/v{random.randint(1,3)}/api/{service}/{action}",
            f"/api/{version}/internal/{service}/{action}"
        ]
        
        return random.choice(paths)
    
    def generate_media_path(self) -> str:
        """Generate realistic media/WebRTC path"""
        services = ['webrtc', 'streaming', 'conference', 'broadcast', 'rtc']
        types = ['signal', 'ice', 'sdp', 'candidate', 'offer', 'answer']
        rooms = ['conference', 'meeting', 'room', 'session', 'call']
        
        service = random.choice(services)
        room_type = random.choice(rooms)
        signal_type = random.choice(types)
        
        paths = [
            f"/media/{service}/{room_type}/{signal_type}",
            f"/streaming/{service}/{signal_type}",
            f"/rtc/{room_type}/{signal_type}",
            f"/ws/{service}/{room_type}",
            f"/socket/{service}/{signal_type}"
        ]
        
        return random.choice(paths)
    
    def generate_health_path(self) -> str:
        """Generate realistic health check path"""
        services = ['microservices', 'services', 'api', 'system', 'internal']
        checks = ['health', 'status', 'ping', 'alive', 'ready', 'heartbeat']
        
        service = random.choice(services)
        check = random.choice(checks)
        
        paths = [
            f"/api/v1/{service}/{check}",
            f"/{service}/{check}",
            f"/internal/{service}/{check}",
            f"/monitoring/{service}/{check}",
            f"/status/{service}/{check}"
        ]
        
        return random.choice(paths)
    
    def generate_endpoints(self, seed: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a complete set of obfuscated endpoints
        
        Args:
            seed: Optional seed for deterministic generation
        
        Returns:
            Dictionary of service names to endpoint paths
        """
        if seed:
            random.seed(seed)
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        generation_id = secrets.token_hex(16)
        
        endpoints = {
            'admin_panel': self.generate_api_path(),
            'xray_websocket': self.generate_js_path(),
            'wireguard_websocket': self.generate_font_path(),
            'trojan_websocket': self.generate_api_path(),
            'health_check': self.generate_health_path(),
            'webrtc_signal': self.generate_media_path(),
            'generated_at': generation_id,
            'timestamp': timestamp,
            'version': '1.0'
        }
        
        if seed:
            random.seed()
        
        return endpoints
    
    def load_endpoints(self) -> Optional[Dict]:
        """Load endpoints from configuration file"""
        try:
            if not self.config_path.exists():
                return None
            
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading endpoints: {e}")
            return None
    
    def save_endpoints(self, endpoints: Dict) -> bool:
        """Save endpoints to configuration file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(endpoints, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving endpoints: {e}")
            return False
    
    def backup_endpoints(self, endpoints: Dict) -> bool:
        """Create a backup of current endpoints"""
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_dir / f'endpoints_{timestamp}.json'
            
            with open(backup_file, 'w') as f:
                json.dump(endpoints, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error backing up endpoints: {e}")
            return False
    
    def should_rotate(self, endpoints: Dict, rotation_days: int = 30) -> bool:
        """
        Check if endpoints should be rotated based on age
        
        Args:
            endpoints: Current endpoints dictionary
            rotation_days: Number of days before rotation is recommended
        
        Returns:
            True if endpoints should be rotated
        """
        if not endpoints or 'timestamp' not in endpoints:
            return True
        
        try:
            timestamp = datetime.fromisoformat(endpoints['timestamp'].replace('Z', '+00:00'))
            age = datetime.utcnow() - timestamp.replace(tzinfo=None)
            return age.days >= rotation_days
        except Exception:
            return False
    
    def rotate_endpoints(self, force: bool = False, rotation_days: int = 30) -> Optional[Dict]:
        """
        Rotate endpoints if needed
        
        Args:
            force: Force rotation regardless of age
            rotation_days: Number of days before rotation
        
        Returns:
            New endpoints if rotation occurred, None otherwise
        """
        current_endpoints = self.load_endpoints()
        
        if not force and current_endpoints:
            if not self.should_rotate(current_endpoints, rotation_days):
                return None
        
        if current_endpoints:
            self.backup_endpoints(current_endpoints)
        
        new_endpoints = self.generate_endpoints()
        
        if self.save_endpoints(new_endpoints):
            return new_endpoints
        
        return None
    
    def validate_endpoints(self, endpoints: Dict) -> Tuple[bool, List[str]]:
        """
        Validate endpoints dictionary
        
        Args:
            endpoints: Endpoints dictionary to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        required_services = [
            'admin_panel',
            'xray_websocket',
            'wireguard_websocket',
            'trojan_websocket'
        ]
        
        required_metadata = ['generated_at', 'timestamp', 'version']
        
        # Check required services
        for service in required_services:
            if service not in endpoints:
                errors.append(f"Missing required service: {service}")
            elif not endpoints[service].startswith('/'):
                errors.append(f"Invalid path for {service}: must start with /")
        
        # Check metadata
        for field in required_metadata:
            if field not in endpoints:
                errors.append(f"Missing required metadata: {field}")
        
        return len(errors) == 0, errors
    
    def get_endpoint_age(self, endpoints: Dict) -> Optional[timedelta]:
        """
        Get the age of endpoints
        
        Args:
            endpoints: Endpoints dictionary
        
        Returns:
            Age as timedelta or None if unable to calculate
        """
        if not endpoints or 'timestamp' not in endpoints:
            return None
        
        try:
            timestamp = datetime.fromisoformat(endpoints['timestamp'].replace('Z', '+00:00'))
            return datetime.utcnow() - timestamp.replace(tzinfo=None)
        except Exception:
            return None
    
    def get_endpoint_by_service(self, service_name: str) -> Optional[str]:
        """
        Get endpoint path for a specific service
        
        Args:
            service_name: Name of the service
        
        Returns:
            Endpoint path or None if not found
        """
        endpoints = self.load_endpoints()
        if not endpoints:
            return None
        
        return endpoints.get(service_name)
    
    def list_services(self) -> List[str]:
        """
        List all configured services
        
        Returns:
            List of service names
        """
        endpoints = self.load_endpoints()
        if not endpoints:
            return []
        
        metadata_keys = ['generated_at', 'timestamp', 'version']
        return [k for k in endpoints.keys() if k not in metadata_keys]
