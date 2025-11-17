#!/usr/bin/env python3
"""
Health monitoring system for Stealth VPN Server
Monitors all services and provides health check endpoints
"""

import json
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result for a service"""
    service: str
    status: ServiceStatus
    message: str
    timestamp: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


@dataclass
class SystemHealth:
    """Overall system health status"""
    status: ServiceStatus
    timestamp: str
    services: List[HealthCheck]
    summary: Dict[str, int]


class HealthMonitor:
    """Monitor health of all VPN services"""
    
    def __init__(self, data_dir: Path = Path("/data/stealth-vpn")):
        self.data_dir = data_dir
        self.health_log = data_dir / "logs" / "health.json"
        self.health_log.parent.mkdir(parents=True, exist_ok=True)
    
    def check_docker_container(self, container_name: str) -> HealthCheck:
        """Check if Docker container is running and healthy"""
        start_time = time.time()
        
        try:
            # Check if container exists and is running
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Status}}", container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if result.returncode != 0:
                return HealthCheck(
                    service=container_name,
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Container not found",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=response_time
                )
            
            status = result.stdout.strip()
            
            if status == "running":
                # Check container health if healthcheck is defined
                health_result = subprocess.run(
                    ["docker", "inspect", "--format={{.State.Health.Status}}", container_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                health_status = health_result.stdout.strip()
                
                if health_status == "healthy" or health_status == "":
                    return HealthCheck(
                        service=container_name,
                        status=ServiceStatus.HEALTHY,
                        message="Container running",
                        timestamp=datetime.now().isoformat(),
                        response_time_ms=response_time
                    )
                elif health_status == "unhealthy":
                    return HealthCheck(
                        service=container_name,
                        status=ServiceStatus.UNHEALTHY,
                        message="Container unhealthy",
                        timestamp=datetime.now().isoformat(),
                        response_time_ms=response_time
                    )
                else:
                    return HealthCheck(
                        service=container_name,
                        status=ServiceStatus.DEGRADED,
                        message=f"Container health: {health_status}",
                        timestamp=datetime.now().isoformat(),
                        response_time_ms=response_time
                    )
            else:
                return HealthCheck(
                    service=container_name,
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Container status: {status}",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=response_time
                )
                
        except subprocess.TimeoutExpired:
            return HealthCheck(
                service=container_name,
                status=ServiceStatus.UNHEALTHY,
                message="Health check timeout",
                timestamp=datetime.now().isoformat(),
                response_time_ms=5000
            )
        except Exception as e:
            return HealthCheck(
                service=container_name,
                status=ServiceStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    def check_xray_service(self) -> HealthCheck:
        """Check Xray service health"""
        container_health = self.check_docker_container("stealth-xray")
        
        if container_health.status != ServiceStatus.HEALTHY:
            return container_health
        
        # Check if config file exists and is valid
        config_file = self.data_dir / "configs" / "xray.json"
        if not config_file.exists():
            return HealthCheck(
                service="xray",
                status=ServiceStatus.DEGRADED,
                message="Config file missing",
                timestamp=datetime.now().isoformat()
            )
        
        try:
            with open(config_file) as f:
                json.load(f)
            
            return HealthCheck(
                service="xray",
                status=ServiceStatus.HEALTHY,
                message="Service operational",
                timestamp=datetime.now().isoformat(),
                response_time_ms=container_health.response_time_ms
            )
        except json.JSONDecodeError:
            return HealthCheck(
                service="xray",
                status=ServiceStatus.DEGRADED,
                message="Invalid config file",
                timestamp=datetime.now().isoformat()
            )
    
    def check_trojan_service(self) -> HealthCheck:
        """Check Trojan service health"""
        container_health = self.check_docker_container("stealth-trojan")
        
        if container_health.status != ServiceStatus.HEALTHY:
            return container_health
        
        config_file = self.data_dir / "configs" / "trojan.json"
        if not config_file.exists():
            return HealthCheck(
                service="trojan",
                status=ServiceStatus.DEGRADED,
                message="Config file missing",
                timestamp=datetime.now().isoformat()
            )
        
        return HealthCheck(
            service="trojan",
            status=ServiceStatus.HEALTHY,
            message="Service operational",
            timestamp=datetime.now().isoformat(),
            response_time_ms=container_health.response_time_ms
        )
    
    def check_singbox_service(self) -> HealthCheck:
        """Check Sing-box service health"""
        container_health = self.check_docker_container("stealth-singbox")
        
        if container_health.status != ServiceStatus.HEALTHY:
            return container_health
        
        config_file = self.data_dir / "configs" / "singbox.json"
        if not config_file.exists():
            return HealthCheck(
                service="singbox",
                status=ServiceStatus.DEGRADED,
                message="Config file missing",
                timestamp=datetime.now().isoformat()
            )
        
        return HealthCheck(
            service="singbox",
            status=ServiceStatus.HEALTHY,
            message="Service operational",
            timestamp=datetime.now().isoformat(),
            response_time_ms=container_health.response_time_ms
        )
    
    def check_wireguard_service(self) -> HealthCheck:
        """Check WireGuard service health"""
        container_health = self.check_docker_container("stealth-wireguard")
        
        if container_health.status != ServiceStatus.HEALTHY:
            return container_health
        
        return HealthCheck(
            service="wireguard",
            status=ServiceStatus.HEALTHY,
            message="Service operational",
            timestamp=datetime.now().isoformat(),
            response_time_ms=container_health.response_time_ms
        )
    
    def check_caddy_service(self) -> HealthCheck:
        """Check Caddy web server health"""
        container_health = self.check_docker_container("stealth-caddy")
        
        if container_health.status != ServiceStatus.HEALTHY:
            return container_health
        
        # Check if Caddy is responding
        try:
            result = subprocess.run(
                ["docker", "exec", "stealth-caddy", "caddy", "validate", "--config", "/etc/caddy/Caddyfile"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return HealthCheck(
                    service="caddy",
                    status=ServiceStatus.HEALTHY,
                    message="Service operational",
                    timestamp=datetime.now().isoformat(),
                    response_time_ms=container_health.response_time_ms
                )
            else:
                return HealthCheck(
                    service="caddy",
                    status=ServiceStatus.DEGRADED,
                    message="Config validation failed",
                    timestamp=datetime.now().isoformat()
                )
        except Exception:
            return container_health
    
    def check_admin_panel(self) -> HealthCheck:
        """Check admin panel health"""
        return self.check_docker_container("stealth-admin")
    
    def check_all_services(self) -> SystemHealth:
        """Check health of all services"""
        checks = [
            self.check_caddy_service(),
            self.check_xray_service(),
            self.check_trojan_service(),
            self.check_singbox_service(),
            self.check_wireguard_service(),
            self.check_admin_panel()
        ]
        
        # Calculate summary
        summary = {
            "healthy": sum(1 for c in checks if c.status == ServiceStatus.HEALTHY),
            "unhealthy": sum(1 for c in checks if c.status == ServiceStatus.UNHEALTHY),
            "degraded": sum(1 for c in checks if c.status == ServiceStatus.DEGRADED),
            "unknown": sum(1 for c in checks if c.status == ServiceStatus.UNKNOWN),
            "total": len(checks)
        }
        
        # Determine overall status
        if summary["unhealthy"] > 0 or summary["unknown"] > 0:
            overall_status = ServiceStatus.UNHEALTHY
        elif summary["degraded"] > 0:
            overall_status = ServiceStatus.DEGRADED
        else:
            overall_status = ServiceStatus.HEALTHY
        
        return SystemHealth(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            services=checks,
            summary=summary
        )
    
    def log_health_check(self, health: SystemHealth) -> None:
        """Log health check results to file"""
        try:
            # Read existing logs
            if self.health_log.exists():
                with open(self.health_log) as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Add new entry
            logs.append({
                "timestamp": health.timestamp,
                "status": health.status.value,
                "summary": health.summary,
                "services": [
                    {
                        "service": c.service,
                        "status": c.status.value,
                        "message": c.message,
                        "response_time_ms": c.response_time_ms
                    }
                    for c in health.services
                ]
            })
            
            # Keep only last 1000 entries
            logs = logs[-1000:]
            
            # Write back
            with open(self.health_log, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Error logging health check: {e}")
    
    def get_health_report(self) -> Dict:
        """Get formatted health report"""
        health = self.check_all_services()
        self.log_health_check(health)
        
        return {
            "status": health.status.value,
            "timestamp": health.timestamp,
            "summary": health.summary,
            "services": [
                {
                    "service": c.service,
                    "status": c.status.value,
                    "message": c.message,
                    "response_time_ms": c.response_time_ms
                }
                for c in health.services
            ]
        }


def main():
    """Run health check and print results"""
    monitor = HealthMonitor()
    report = monitor.get_health_report()
    
    print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    if report["status"] == "healthy":
        exit(0)
    elif report["status"] == "degraded":
        exit(1)
    else:
        exit(2)


if __name__ == "__main__":
    main()
