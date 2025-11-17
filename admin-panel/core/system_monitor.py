"""
System monitoring module for collecting server and container metrics.
"""

import psutil
import docker
from typing import Dict, Any, Optional
from datetime import datetime


class SystemMonitor:
    """Monitor system resources and Docker container statistics."""
    
    def __init__(self):
        """Initialize system monitor with Docker client."""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            print(f"Warning: Could not initialize Docker client: {e}")
            self.docker_client = None
    
    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.
        
        Returns:
            float: CPU usage percentage (0-100)
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            print(f"Error getting CPU usage: {e}")
            return 0.0
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        Get memory usage statistics.
        
        Returns:
            dict: Memory statistics with total, used, available, and percent
        """
        try:
            mem = psutil.virtual_memory()
            return {
                'total': mem.total,
                'used': mem.used,
                'available': mem.available,
                'percent': mem.percent
            }
        except Exception as e:
            print(f"Error getting memory usage: {e}")
            return {
                'total': 0,
                'used': 0,
                'available': 0,
                'percent': 0.0
            }
    
    def get_disk_usage(self, path: str = '/app/data') -> Dict[str, Any]:
        """
        Get disk usage for specified path.
        
        Args:
            path: Path to check disk usage for
            
        Returns:
            dict: Disk statistics with total, used, free, and percent
        """
        try:
            disk = psutil.disk_usage(path)
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except Exception as e:
            print(f"Error getting disk usage for {path}: {e}")
            return {
                'total': 0,
                'used': 0,
                'free': 0,
                'percent': 0.0
            }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get network I/O statistics.
        
        Returns:
            dict: Network statistics with bytes and packets sent/received
        """
        try:
            net = psutil.net_io_counters()
            return {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv,
                'packets_sent': net.packets_sent,
                'packets_recv': net.packets_recv
            }
        except Exception as e:
            print(f"Error getting network stats: {e}")
            return {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get all system metrics in one call.
        
        Returns:
            dict: Complete system metrics including CPU, memory, disk, and network
        """
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_stats(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """
        Calculate CPU percentage from Docker stats.
        
        Args:
            stats: Docker container stats dictionary
            
        Returns:
            float: CPU usage percentage
        """
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_count = stats['cpu_stats'].get('online_cpus', 1)
                return (cpu_delta / system_delta) * cpu_count * 100.0
            return 0.0
        except (KeyError, ZeroDivisionError, TypeError):
            return 0.0
    
    def get_container_stats(self, container_name: str) -> Dict[str, Any]:
        """
        Get Docker container statistics.
        
        Args:
            container_name: Name of the container
            
        Returns:
            dict: Container statistics including status, CPU, memory, and network
        """
        if not self.docker_client:
            return {'error': 'Docker client not available'}
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            # Get container status
            status = container.status
            
            # Get stats (non-streaming)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_percent = self._calculate_cpu_percent(stats)
            
            # Get memory usage
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 0)
            memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0.0
            
            # Get network stats
            networks = stats.get('networks', {})
            network_rx = 0
            network_tx = 0
            
            for net_name, net_stats in networks.items():
                network_rx += net_stats.get('rx_bytes', 0)
                network_tx += net_stats.get('tx_bytes', 0)
            
            return {
                'status': status,
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage': memory_usage,
                'memory_limit': memory_limit,
                'memory_percent': round(memory_percent, 2),
                'network_rx': network_rx,
                'network_tx': network_tx
            }
        except docker.errors.NotFound:
            return {'error': f'Container {container_name} not found', 'status': 'not_found'}
        except Exception as e:
            return {'error': str(e), 'status': 'error'}
    
    def get_all_service_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all VPN services.
        
        Returns:
            dict: Statistics for each service (xray, trojan, singbox, wireguard, caddy, admin)
        """
        services = ['xray', 'trojan', 'singbox', 'wireguard', 'caddy', 'admin']
        service_stats = {}
        
        for service in services:
            container_name = f'stealth-{service}'
            service_stats[service] = self.get_container_stats(container_name)
        
        return service_stats
