"""
Log Reader Module
Reads and filters Docker container logs for VPN services.
"""

import docker
from typing import List, Dict, Optional
from datetime import datetime
import re


class LogReader:
    """Read and filter logs from Docker containers."""
    
    def __init__(self):
        """Initialize Docker client."""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Warning: Could not initialize Docker client: {e}")
            self.docker_client = None
    
    def get_container_logs(
        self, 
        container_name: str, 
        lines: int = 100,
        level_filter: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Read logs from Docker container.
        
        Args:
            container_name: Name of the Docker container
            lines: Number of lines to retrieve (tail)
            level_filter: Filter by log level (INFO, WARNING, ERROR)
        
        Returns:
            List of log entries with timestamp and message
        """
        if not self.docker_client:
            return [{'timestamp': '', 'message': 'Docker client not available'}]
        
        try:
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8', errors='replace')
            
            log_lines = logs.strip().split('\n')
            parsed_logs = []
            
            for line in log_lines:
                if not line.strip():
                    continue
                
                # Parse timestamp and message
                # Docker log format: "2024-01-01T12:00:00.000000000Z message"
                parsed = self._parse_log_line(line)
                
                # Filter by log level if specified
                if level_filter:
                    if not self._matches_level(parsed['message'], level_filter):
                        continue
                
                parsed_logs.append(parsed)
            
            return parsed_logs
        except docker.errors.NotFound:
            return [{'timestamp': '', 'message': f'Container {container_name} not found'}]
        except Exception as e:
            return [{'timestamp': '', 'message': f'Error reading logs: {str(e)}'}]
    
    def _parse_log_line(self, line: str) -> Dict[str, str]:
        """
        Parse a Docker log line into timestamp and message.
        
        Args:
            line: Raw log line from Docker
        
        Returns:
            Dictionary with timestamp and message
        """
        # Docker timestamp format: 2024-01-01T12:00:00.000000000Z
        timestamp_pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+'
        match = re.match(timestamp_pattern, line)
        
        if match:
            timestamp = match.group(1)
            message = line[match.end():]
            
            # Format timestamp for display (remove nanoseconds)
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_timestamp = timestamp[:19]  # Just take YYYY-MM-DD HH:MM:SS
            
            return {
                'timestamp': formatted_timestamp,
                'message': message
            }
        else:
            # No timestamp found, return as-is
            return {
                'timestamp': '',
                'message': line
            }
    
    def _matches_level(self, message: str, level_filter: str) -> bool:
        """
        Check if log message matches the specified level.
        
        Args:
            message: Log message text
            level_filter: Level to filter (INFO, WARNING, ERROR)
        
        Returns:
            True if message matches the level
        """
        level_upper = level_filter.upper()
        message_upper = message.upper()
        
        # Common log level patterns
        level_patterns = {
            'ERROR': ['ERROR', 'ERR', 'FATAL', 'CRITICAL'],
            'WARNING': ['WARNING', 'WARN', 'WRN'],
            'INFO': ['INFO', 'INF']
        }
        
        patterns = level_patterns.get(level_upper, [level_upper])
        
        for pattern in patterns:
            if pattern in message_upper:
                return True
        
        return False
    
    def get_service_logs(
        self, 
        service: str, 
        lines: int = 100,
        level_filter: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Get logs for a VPN service.
        
        Args:
            service: Service name (xray, trojan, singbox, wireguard, caddy, admin)
            lines: Number of lines to retrieve
            level_filter: Filter by log level
        
        Returns:
            Dictionary with service info and logs
        """
        # Map service names to container names
        container_map = {
            'xray': 'stealth-xray',
            'trojan': 'stealth-trojan',
            'singbox': 'stealth-singbox',
            'wireguard': 'stealth-wireguard',
            'caddy': 'stealth-caddy',
            'admin': 'stealth-admin'
        }
        
        container_name = container_map.get(service, f'stealth-{service}')
        
        logs = self.get_container_logs(container_name, lines, level_filter)
        
        return {
            'service': service,
            'container': container_name,
            'logs': logs,
            'count': len(logs)
        }
    
    def get_caddy_access_logs(self, lines: int = 100) -> List[Dict[str, str]]:
        """
        Get Caddy access logs (separate from error logs).
        
        Args:
            lines: Number of lines to retrieve
        
        Returns:
            List of access log entries
        """
        # Caddy access logs are typically in the container logs
        # We filter for lines that look like HTTP access logs
        logs = self.get_container_logs('stealth-caddy', lines * 2)  # Get more to filter
        
        access_logs = []
        for log in logs:
            message = log['message']
            # Access logs typically contain HTTP methods and status codes
            if any(method in message for method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']):
                if any(code in message for code in ['200', '201', '204', '301', '302', '304', '400', '401', '403', '404', '500', '502', '503']):
                    access_logs.append(log)
        
        # Return only requested number of lines
        return access_logs[:lines]
    
    def get_caddy_error_logs(self, lines: int = 100) -> List[Dict[str, str]]:
        """
        Get Caddy error logs (separate from access logs).
        
        Args:
            lines: Number of lines to retrieve
        
        Returns:
            List of error log entries
        """
        # Get all logs and filter for errors
        logs = self.get_container_logs('stealth-caddy', lines * 2, level_filter='ERROR')
        
        # Also include warnings
        warning_logs = self.get_container_logs('stealth-caddy', lines * 2, level_filter='WARNING')
        
        # Combine and sort by timestamp
        all_error_logs = logs + warning_logs
        
        # Remove duplicates and sort
        seen = set()
        unique_logs = []
        for log in all_error_logs:
            log_key = f"{log['timestamp']}:{log['message']}"
            if log_key not in seen:
                seen.add(log_key)
                unique_logs.append(log)
        
        # Return only requested number of lines
        return unique_logs[:lines]
