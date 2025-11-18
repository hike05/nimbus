"""
Core interfaces for the Multi-Protocol Proxy Server system.
Defines the system boundaries and contracts between components.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


@dataclass
class User:
    """User data model for proxy access with validation."""
    username: str
    id: str  # UUID
    xray_uuid: str
    wireguard_private_key: str
    wireguard_public_key: str
    trojan_password: str
    # Sing-box protocol credentials
    shadowtls_password: Optional[str] = None
    shadowsocks_password: Optional[str] = None
    hysteria2_password: Optional[str] = None
    tuic_uuid: Optional[str] = None
    tuic_password: Optional[str] = None
    created_at: str = ""  # ISO format
    last_seen: Optional[str] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Validate user data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate user data fields."""
        # Username validation
        if not self.username or not isinstance(self.username, str):
            raise ValueError("Username must be a non-empty string")
        if not re.match(r'^[a-zA-Z0-9_-]{3,32}$', self.username):
            raise ValueError("Username must be 3-32 characters, alphanumeric with _ or -")
        
        # UUID validation
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, self.id.lower()):
            raise ValueError(f"Invalid user ID format: {self.id}")
        if not re.match(uuid_pattern, self.xray_uuid.lower()):
            raise ValueError(f"Invalid Xray UUID format: {self.xray_uuid}")
        if self.tuic_uuid and not re.match(uuid_pattern, self.tuic_uuid.lower()):
            raise ValueError(f"Invalid TUIC UUID format: {self.tuic_uuid}")
        
        # Key validation
        if not self.wireguard_private_key or len(self.wireguard_private_key) < 32:
            raise ValueError("WireGuard private key must be at least 32 characters")
        if not self.wireguard_public_key or len(self.wireguard_public_key) < 32:
            raise ValueError("WireGuard public key must be at least 32 characters")
        
        # Password validation
        if not self.trojan_password or len(self.trojan_password) < 16:
            raise ValueError("Trojan password must be at least 16 characters")
        
        # Date validation
        if self.created_at:
            try:
                datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid created_at date format: {self.created_at}")
        
        if self.last_seen:
            try:
                datetime.fromisoformat(self.last_seen.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid last_seen date format: {self.last_seen}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User instance from dictionary with validation."""
        return cls(**data)


@dataclass
class ServerConfig:
    """Server configuration data model with validation."""
    wireguard_server_private_key: str
    wireguard_server_public_key: str
    xray_private_key: str
    admin_password_hash: str
    session_secret: str
    obfuscated_endpoints: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    
    def __post_init__(self):
        """Validate server configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate server configuration fields."""
        if not self.wireguard_server_private_key or len(self.wireguard_server_private_key) < 32:
            raise ValueError("WireGuard server private key must be at least 32 characters")
        if not self.wireguard_server_public_key or len(self.wireguard_server_public_key) < 32:
            raise ValueError("WireGuard server public key must be at least 32 characters")
        if not self.xray_private_key or len(self.xray_private_key) < 32:
            raise ValueError("Xray private key must be at least 32 characters")
        if not self.admin_password_hash:
            raise ValueError("Admin password hash cannot be empty")
        if not self.session_secret or len(self.session_secret) < 32:
            raise ValueError("Session secret must be at least 32 characters")
        if not isinstance(self.obfuscated_endpoints, dict):
            raise ValueError("Obfuscated endpoints must be a dictionary")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert server config to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServerConfig':
        """Create ServerConfig instance from dictionary with validation."""
        return cls(**data)


@dataclass
class ClientConfig:
    """Base client configuration."""
    protocol: str
    server_address: str
    server_port: int


@dataclass
class XrayConfig(ClientConfig):
    """Xray client configuration."""
    user_uuid: str
    flow: Optional[str]
    tls_server_name: str
    websocket_path: Optional[str]


@dataclass
class WireGuardConfig(ClientConfig):
    """WireGuard client configuration."""
    private_key: str
    server_public_key: str
    allowed_ips: List[str]
    dns_servers: List[str]
    transport_method: str  # "websocket", "udp2raw", "native"
    websocket_path: Optional[str]
    tls_server_name: Optional[str]


@dataclass
class TrojanConfig(ClientConfig):
    """Trojan-Go client configuration."""
    password: str
    sni: str
    websocket_enabled: bool
    websocket_path: Optional[str]
    websocket_host: Optional[str]
    fingerprint: str
    alpn: List[str]


@dataclass
class ShadowTLSConfig(ClientConfig):
    """ShadowTLS v3 client configuration."""
    password: str
    sni: str
    version: int
    handshake_server: str
    handshake_port: int


@dataclass
class Hysteria2Config(ClientConfig):
    """Hysteria 2 client configuration."""
    password: str
    sni: str
    obfs_password: str
    up_mbps: int
    down_mbps: int
    alpn: List[str]


@dataclass
class TuicConfig(ClientConfig):
    """TUIC v5 client configuration."""
    uuid: str
    password: str
    sni: str
    congestion_control: str
    alpn: List[str]


class UserStorageInterface(ABC):
    """Interface for user data storage operations."""
    
    @abstractmethod
    def load_users(self) -> Dict[str, User]:
        """Load all users from storage."""
        pass
    
    @abstractmethod
    def save_users(self, users: Dict[str, User]) -> None:
        """Save users to storage with backup."""
        pass
    
    @abstractmethod
    def add_user(self, username: str) -> User:
        """Create a new user with generated credentials."""
        pass
    
    @abstractmethod
    def remove_user(self, username: str) -> bool:
        """Remove user from storage."""
        pass
    
    @abstractmethod
    def get_user(self, username: str) -> Optional[User]:
        """Get specific user by username."""
        pass


class ConfigGeneratorInterface(ABC):
    """Interface for generating proxy server and client configurations."""
    
    @abstractmethod
    def generate_xray_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Xray server configuration."""
        pass
    
    @abstractmethod
    def generate_wireguard_server_config(self, users: Dict[str, User]) -> str:
        """Generate WireGuard server configuration."""
        pass
    
    @abstractmethod
    def generate_trojan_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Trojan-Go server configuration."""
        pass
    
    @abstractmethod
    def generate_singbox_server_config(self, users: Dict[str, User]) -> Dict[str, Any]:
        """Generate Sing-box server configuration."""
        pass
    
    @abstractmethod
    def generate_client_configs(self, username: str, user: User) -> Dict[str, str]:
        """Generate all client configurations for a user."""
        pass
    
    @abstractmethod
    def update_server_configs(self) -> bool:
        """Update all server configurations and reload services."""
        pass


class ObfuscationInterface(ABC):
    """Interface for endpoint obfuscation management."""
    
    @abstractmethod
    def generate_obfuscated_endpoints(self) -> Dict[str, str]:
        """Generate realistic obfuscated endpoint paths."""
        pass
    
    @abstractmethod
    def rotate_endpoints(self) -> bool:
        """Rotate obfuscated endpoints and update configurations."""
        pass
    
    @abstractmethod
    def get_current_endpoints(self) -> Dict[str, str]:
        """Get currently active obfuscated endpoints."""
        pass


class ServiceManagerInterface(ABC):
    """Interface for managing proxy services."""
    
    @abstractmethod
    def reload_service(self, service_name: str) -> bool:
        """Gracefully reload a proxy service."""
        pass
    
    @abstractmethod
    def check_service_health(self, service_name: str) -> bool:
        """Check if a service is running and healthy."""
        pass
    
    @abstractmethod
    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all proxy services."""
        pass


class AuthenticationInterface(ABC):
    """Interface for admin panel authentication."""
    
    @abstractmethod
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate admin user."""
        pass
    
    @abstractmethod
    def create_session(self, username: str) -> str:
        """Create authenticated session token."""
        pass
    
    @abstractmethod
    def validate_session(self, token: str) -> bool:
        """Validate session token."""
        pass
    
    @abstractmethod
    def revoke_session(self, token: str) -> None:
        """Revoke session token."""
        pass


class WebServiceInterface(ABC):
    """Interface for the cover web service."""
    
    @abstractmethod
    def serve_cover_page(self) -> str:
        """Serve the cover web page content."""
        pass
    
    @abstractmethod
    def serve_api_docs(self) -> str:
        """Serve fake API documentation."""
        pass
    
    @abstractmethod
    def handle_admin_panel(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle admin panel requests with obfuscation."""
        pass
