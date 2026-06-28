#!/usr/bin/env python3
"""
Brotherhood Omega Swarm Health Monitor CLI

Monitor container health, track uptime, diagnose issues, and send alerts.

Usage:
    python bin/monitor.py status              # Show current swarm health
    python bin/monitor.py watch              # Continuous monitoring mode
    python bin/monitor.py history SERVICE    # Show service history
    python bin/monitor.py diagnose           # Diagnose unhealthy services
    python bin/monitor.py alert              # Send health report to Telegram
"""

import asyncio
import sys
import logging
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.monitoring import (
    SwarmMonitor, DiagnosticAnalyzer, HealthStatus, get_monitor
)
from core.alerts import get_alert_manager, TelegramAlerter
from core.config import settings


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthMonitorCLI:
    """CLI for swarm health monitoring"""
    
    def __init__(self, monitor: SwarmMonitor):
        self.monitor = monitor
        self.alert_manager = get_alert_manager()
    
    async def show_status(self):
        """Display current swarm health status"""
        print("\n" + "="*80)
        print("🔱 BROTHERHOOD OMEGA SWARM HEALTH STATUS")
        print("="*80)
        print(f"Time: {datetime.utcnow().isoformat()}")
        print(f"Target: {self.monitor.base_url}")
        print()
        
        # Get health
        print("Checking services...\n")
        health = await self.monitor.check_all_services()
        
        # Summary
        print(f"Overall Status: {health.overall_status.value.upper()}")
        print(f"Health Score: {health.health_percentage:.1f}%")
        print(f"Healthy: {health.healthy_count}/{health.total_services}")
        print()
        
        # Per-service details
        print("Services:")
        print("-" * 80)
        print(f"{'Service':<30} {'Status':<15} {'Port':<8} {'Response':<15} {'Error':<20}")
        print("-" * 80)
        
        for check in health.checks:
            status_icon = (
                "✅" if check.status == HealthStatus.HEALTHY
                else "❌" if check.status == HealthStatus.UNHEALTHY
                else "❓"
            )
            
            status_text = f"{status_icon} {check.status.value}"
            response = f"{check.response_time_ms:.0f}ms" if check.response_time_ms else "N/A"
            error = check.error_message[:20] if check.error_message else "-"
            
            print(
                f"{check.service_name:<30} {status_text:<15} "
                f"{check.port:<8} {response:<15} {error:<20}"
            )
        
        print("-" * 80)
        print()
        
        return health
    
    async def watch_status(self, interval: int = 30, duration: Optional[int] = None):
        """
        Continuously monitor swarm health
        
        Args:
            interval: Check interval in seconds
            duration: Stop after N seconds (None = infinite)
        """
        print(f"\n🔍 Starting continuous monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        elapsed = 0
        prev_status = None
        
        try:
            while True:
                if duration and elapsed >= duration:
                    break
                
                health = await self.show_status()
                
                # Check for status changes
                if prev_status != health.overall_status:
                    print(f"⚠️  Status change: {prev_status} → {health.overall_status}")
                    
                    # Alert on status change
                    if health.overall_status != HealthStatus.HEALTHY:
                        await self.alert_manager.alert_swarm_unhealthy(health)
                
                prev_status = health.overall_status
                
                # Wait before next check
                print(f"Next check in {interval}s (Ctrl+C to stop)...\n")
                await asyncio.sleep(interval)
                elapsed += interval
                
        except KeyboardInterrupt:
            print("\n\n✋ Monitoring stopped")
    
    async def show_history(self, service_name: str):
        """Show health history for a service"""
        print("\n" + "="*80)
        print(f"📊 HISTORY: {service_name}")
        print("="*80)
        
        # Check if we have history
        if service_name not in self.monitor.health_history:
            print(f"❌ No history found for {service_name}")
            print("Run 'status' command first to build history")
            return
        
        history = self.monitor.health_history[service_name]
        
        # Show last 20 checks
        print(f"Showing last {min(20, len(history))} checks:\n")
        print(f"{'Time':<25} {'Status':<12} {'Response':<12} {'Error':<30}")
        print("-" * 80)
        
        for check in history[-20:]:
            status_icon = (
                "✅" if check.status == HealthStatus.HEALTHY
                else "❌" if check.status == HealthStatus.UNHEALTHY
                else "❓"
            )
            response = f"{check.response_time_ms:.0f}ms" if check.response_time_ms else "N/A"
            error = check.error_message[:30] if check.error_message else "-"
            
            time_short = check.checked_at[-8:] if check.checked_at else "?"
            
            print(
                f"{time_short:<25} {status_icon} {check.status.value:<10} "
                f"{response:<12} {error:<30}"
            )
        
        print()
        
        # Show trends
        print("Trends:")
        print("-" * 80)
        
        for window in [60, 300, 3600]:
            trend = self.monitor.get_trend(service_name, window_seconds=window)
            if "error" not in trend:
                window_min = window // 60
                uptime = trend.get("uptime_pct", 0)
                avg_time = trend.get("avg_response_time_ms", 0)
                samples = trend.get("samples", 0)
                
                print(
                    f"Last {window_min}m: {uptime:.1f}% uptime "
                    f"({samples} samples, avg {avg_time:.0f}ms)"
                )
    
    async def diagnose(self):
        """Diagnose unhealthy services"""
        print("\n" + "="*80)
        print("🔍 DIAGNOSTICS")
        print("="*80 + "\n")
        
        health = await self.show_status()
        
        if health.overall_status == HealthStatus.HEALTHY:
            print("✅ All services healthy - no issues found\n")
            return
        
        print("\nAnalyzing failures...\n")
        diagnostics = DiagnosticAnalyzer.diagnose_failures(health)
        
        # Common issues
        if diagnostics["common_issues"]:
            print("🚨 Common Issues:")
            for issue in diagnostics["common_issues"]:
                print(f"  • {issue}")
            print()
        
        # Per-service issues
        if diagnostics["issues_by_service"]:
            print("Per-Service Diagnosis:")
            print("-" * 80)
            
            for service, diag in diagnostics["issues_by_service"].items():
                print(f"\n{service}:")
                print(f"  Error: {diag['error']}")
                
                if diag["possible_causes"]:
                    print("  Possible causes:")
                    for cause in diag["possible_causes"]:
                        print(f"    - {cause}")
                
                if diag["debugging_steps"]:
                    print("  Debugging steps:")
                    for step in diag["debugging_steps"]:
                        print(f"    $ {step}")
        
        # Recommended fixes
        if diagnostics["recommended_fixes"]:
            print("\n" + "="*80)
            print("Recommended Fixes (in order):")
            print("="*80)
            
            for i, fix in enumerate(diagnostics["recommended_fixes"], 1):
                print(f"{i}. {fix}")
        
        print()
    
    async def send_alert(self):
        """Send current health status to Telegram"""
        print("\n📤 Sending health report to Telegram...\n")
        
        health = await self.monitor.check_all_services()
        
        success = await self.alert_manager.alerter.send_swarm_health_report(health)
        
        if success:
            print("✅ Alert sent successfully")
        else:
            print("❌ Failed to send alert")
            print(f"Bot token: {bool(settings.TELEGRAM_BOT_TOKEN)}")
            print(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
        
        print()


async def main():
    """Main CLI entry point"""
    
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Initialize monitor
    monitor = get_monitor(base_url="http://206.189.118.255")
    cli = HealthMonitorCLI(monitor)
    
    try:
        if command == "status":
            await cli.show_status()
        
        elif command == "watch":
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            await cli.watch_status(interval=interval)
        
        elif command == "history":
            if len(sys.argv) < 3:
                print("Usage: monitor.py history <service_name>")
                sys.exit(1)
            service = sys.argv[2]
            await cli.show_history(service)
        
        elif command == "diagnose":
            await cli.diagnose()
        
        elif command == "alert":
            await cli.send_alert()
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
