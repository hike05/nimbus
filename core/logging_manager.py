#!/usr/bin/env python3
"""
Centralized logging manager for Multi-Protocol Proxy Server
Implements security-focused logging (no IP addresses)
"""

import json
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import re


class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs"""
    
    # Patterns to detect and anonymize
    IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    IPV6_PATTERN = re.compile(r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    def __init__(self, anonymize_ips: bool = True):
        super().__init__()
        self.anonymize_ips = anonymize_ips
        self._ip_cache = {}
    
    def _anonymize_ip(self, ip: str) -> str:
        """Anonymize IP address using consistent hashing"""
        if ip not in self._ip_cache:
            # Create consistent hash for the IP
            hash_obj = hashlib.sha256(ip.encode())
            hash_hex = hash_obj.hexdigest()[:8]
            self._ip_cache[ip] = f"user_{hash_hex}"
        return self._ip_cache[ip]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and anonymize log records"""
        if self.anonymize_ips:
            # Anonymize IP addresses in message
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                # Replace IPv4 addresses
                record.msg = self.IP_PATTERN.sub(
                    lambda m: self._anonymize_ip(m.group(0)),
                    record.msg
                )
                # Replace IPv6 addresses
                record.msg = self.IPV6_PATTERN.sub(
                    lambda m: self._anonymize_ip(m.group(0)),
                    record.msg
                )
            
            # Anonymize in args if present
            if hasattr(record, 'args') and record.args:
                new_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        arg = self.IP_PATTERN.sub(
                            lambda m: self._anonymize_ip(m.group(0)),
                            arg
                        )
                        arg = self.IPV6_PATTERN.sub(
                            lambda m: self._anonymize_ip(m.group(0)),
                            arg
                        )
                    new_args.append(arg)
                record.args = tuple(new_args)
        
        return True


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class LoggingManager:
    """Manage centralized logging for all services"""
    
    def __init__(
        self,
        log_dir: Path = Path("/data/proxy/logs"),
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        anonymize_ips: bool = True
    ):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.anonymize_ips = anonymize_ips
        
        # Create subdirectories for each service
        self.service_dirs = {
            'xray': self.log_dir / 'xray',
            'trojan': self.log_dir / 'trojan',
            'singbox': self.log_dir / 'singbox',
            'wireguard': self.log_dir / 'wireguard',
            'caddy': self.log_dir / 'caddy',
            'admin': self.log_dir / 'admin',
            'system': self.log_dir / 'system'
        }
        
        for service_dir in self.service_dirs.values():
            service_dir.mkdir(parents=True, exist_ok=True)
    
    def get_logger(
        self,
        name: str,
        service: str = 'system',
        level: int = logging.INFO,
        json_format: bool = False
    ) -> logging.Logger:
        """Get or create a logger for a service"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Determine log file path
        service_dir = self.service_dirs.get(service, self.service_dirs['system'])
        log_file = service_dir / f"{name}.log"
        
        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        # Set formatter
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        handler.setFormatter(formatter)
        
        # Add security filter
        security_filter = SecurityFilter(anonymize_ips=self.anonymize_ips)
        handler.addFilter(security_filter)
        
        logger.addHandler(handler)
        
        # Also add console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(security_filter)
        logger.addHandler(console_handler)
        
        return logger
    
    def cleanup_old_logs(self, days: int = 7) -> Dict[str, int]:
        """Clean up logs older than specified days"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = {}
        
        for service, service_dir in self.service_dirs.items():
            count = 0
            for log_file in service_dir.glob('*.log*'):
                try:
                    # Check file modification time
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime < cutoff_time:
                        log_file.unlink()
                        count += 1
                except Exception as e:
                    print(f"Error deleting {log_file}: {e}")
            
            if count > 0:
                deleted_count[service] = count
        
        return deleted_count
    
    def get_log_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics about log files"""
        stats = {}
        
        for service, service_dir in self.service_dirs.items():
            log_files = list(service_dir.glob('*.log*'))
            total_size = sum(f.stat().st_size for f in log_files)
            
            stats[service] = {
                'file_count': len(log_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'directory': str(service_dir)
            }
        
        return stats
    
    def rotate_all_logs(self) -> Dict[str, bool]:
        """Force rotation of all log files"""
        results = {}
        
        # Get all active loggers
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            for handler in logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    try:
                        handler.doRollover()
                        results[logger_name] = True
                    except Exception as e:
                        print(f"Error rotating {logger_name}: {e}")
                        results[logger_name] = False
        
        return results


def setup_service_logging(
    service_name: str,
    log_level: str = "INFO",
    anonymize_ips: bool = True
) -> logging.Logger:
    """
    Setup logging for a service
    
    Args:
        service_name: Name of the service (xray, trojan, etc.)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        anonymize_ips: Whether to anonymize IP addresses
    
    Returns:
        Configured logger instance
    """
    manager = LoggingManager(anonymize_ips=anonymize_ips)
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    logger = manager.get_logger(
        name=service_name,
        service=service_name,
        level=level,
        json_format=False
    )
    
    return logger


def main():
    """Test logging functionality"""
    manager = LoggingManager()
    
    # Test logger
    logger = manager.get_logger('test', 'system')
    logger.info("Test log message")
    logger.info("Connection from 192.168.1.100")
    logger.warning("Failed login attempt from 10.0.0.5")
    
    # Get stats
    stats = manager.get_log_stats()
    print("\nLog Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Cleanup test
    deleted = manager.cleanup_old_logs(days=7)
    if deleted:
        print(f"\nDeleted old logs: {deleted}")


if __name__ == "__main__":
    main()
