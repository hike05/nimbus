#!/usr/bin/env python3
"""
Service monitoring script for Multi-Protocol Proxy Server
Continuously monitors all services and provides alerts
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.health_monitor import HealthMonitor, ServiceStatus


class ServiceMonitor:
    """Continuous service monitoring with alerting"""
    
    def __init__(self, data_dir: Path, alert_threshold: int = 3):
        self.monitor = HealthMonitor(data_dir)
        self.alert_threshold = alert_threshold
        self.failure_counts = {}
        self.alert_log = data_dir / "logs" / "alerts.json"
        self.alert_log.parent.mkdir(parents=True, exist_ok=True)
    
    def log_alert(self, service: str, message: str, severity: str = "warning"):
        """Log an alert to file"""
        try:
            if self.alert_log.exists():
                with open(self.alert_log) as f:
                    alerts = json.load(f)
            else:
                alerts = []
            
            alert = {
                "timestamp": datetime.now().isoformat(),
                "service": service,
                "severity": severity,
                "message": message
            }
            
            alerts.append(alert)
            
            # Keep only last 500 alerts
            alerts = alerts[-500:]
            
            with open(self.alert_log, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            # Print to console
            print(f"[{severity.upper()}] {service}: {message}")
            
        except Exception as e:
            print(f"Error logging alert: {e}")
    
    def check_and_alert(self):
        """Check all services and generate alerts if needed"""
        health = self.monitor.check_all_services()
        
        for check in health.services:
            service = check.service
            
            # Initialize failure count
            if service not in self.failure_counts:
                self.failure_counts[service] = 0
            
            # Check service status
            if check.status == ServiceStatus.UNHEALTHY:
                self.failure_counts[service] += 1
                
                if self.failure_counts[service] >= self.alert_threshold:
                    self.log_alert(
                        service,
                        f"Service unhealthy: {check.message}",
                        severity="critical"
                    )
                elif self.failure_counts[service] == 1:
                    self.log_alert(
                        service,
                        f"Service became unhealthy: {check.message}",
                        severity="warning"
                    )
            
            elif check.status == ServiceStatus.DEGRADED:
                self.log_alert(
                    service,
                    f"Service degraded: {check.message}",
                    severity="warning"
                )
                self.failure_counts[service] = 0
            
            else:
                # Service is healthy
                if self.failure_counts[service] > 0:
                    self.log_alert(
                        service,
                        "Service recovered",
                        severity="info"
                    )
                self.failure_counts[service] = 0
        
        return health
    
    def run_continuous(self, interval: int = 30):
        """Run continuous monitoring"""
        print(f"Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                health = self.check_and_alert()
                
                # Print summary
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"Status: {health.status.value.upper()} | "
                      f"Healthy: {health.summary['healthy']}/{health.summary['total']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")
    
    def run_once(self):
        """Run single health check"""
        health = self.check_and_alert()
        
        # Print detailed report
        print("\n" + "="*60)
        print(f"Health Check Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"\nOverall Status: {health.status.value.upper()}")
        print(f"\nSummary:")
        print(f"  Healthy:   {health.summary['healthy']}")
        print(f"  Degraded:  {health.summary['degraded']}")
        print(f"  Unhealthy: {health.summary['unhealthy']}")
        print(f"  Unknown:   {health.summary['unknown']}")
        print(f"  Total:     {health.summary['total']}")
        
        print(f"\nService Details:")
        for check in health.services:
            status_symbol = {
                ServiceStatus.HEALTHY: "✓",
                ServiceStatus.DEGRADED: "⚠",
                ServiceStatus.UNHEALTHY: "✗",
                ServiceStatus.UNKNOWN: "?"
            }.get(check.status, "?")
            
            response_time = f" ({check.response_time_ms:.0f}ms)" if check.response_time_ms else ""
            print(f"  {status_symbol} {check.service:15} {check.status.value:10} - {check.message}{response_time}")
        
        print("\n" + "="*60 + "\n")
        
        # Exit with appropriate code
        if health.status == ServiceStatus.HEALTHY:
            return 0
        elif health.status == ServiceStatus.DEGRADED:
            return 1
        else:
            return 2


def main():
    parser = argparse.ArgumentParser(description="Monitor Multi-Protocol Proxy services")
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous monitoring"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./data/proxy"),
        help="Data directory path"
    )
    parser.add_argument(
        "--alert-threshold",
        type=int,
        default=3,
        help="Number of failures before critical alert (default: 3)"
    )
    
    args = parser.parse_args()
    
    monitor = ServiceMonitor(args.data_dir, args.alert_threshold)
    
    if args.continuous:
        monitor.run_continuous(args.interval)
    else:
        exit_code = monitor.run_once()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
