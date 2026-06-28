#!/usr/bin/env python3
"""
Cron-friendly monitoring script for continuous swarm health checks.

This script is designed to be run via cron (e.g., every 5 minutes):
  */5 * * * * cd /opt/omega-dynasty-v6 && python bin/monitor_cron.py

It performs lightweight health checks and sends alerts only when:
- Services transition from healthy → unhealthy
- Services transition from unhealthy → healthy
- Overall swarm health changes
- Critical failures occur (multiple services down)

Usage:
  python bin/monitor_cron.py              # Run single check
  python bin/monitor_cron.py --interval 60  # Run every 60 seconds
  python bin/monitor_cron.py --daemon       # Run as daemon (background)
"""

import asyncio
import sys
import logging
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.monitoring import (
    SwarmMonitor, HealthStatus, get_monitor
)
from core.alerts import get_alert_manager, get_alerter
from core.config import settings


# Setup logging - write to file for cron jobs
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "monitor.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CronMonitor:
    """Lightweight cron-friendly monitor"""
    
    STATE_FILE = LOG_DIR / "monitor_state.json"
    
    def __init__(self, monitor: SwarmMonitor = None):
        self.monitor = monitor or get_monitor()
        self.alert_manager = get_alert_manager()
        self.alerter = get_alerter()
        self.state = self._load_state()
        self.logger = logging.getLogger(__name__)
    
    def _load_state(self) -> Dict:
        """Load previous state from file"""
        if self.STATE_FILE.exists():
            try:
                with open(self.STATE_FILE) as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}")
        
        return {
            "last_check": None,
            "last_overall_status": None,
            "service_status": {},
            "last_alert_time": None,
        }
    
    def _save_state(self):
        """Save state to file"""
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save state: {e}")
    
    async def check_and_alert(self) -> bool:
        """
        Check swarm health and send alerts if status changed
        
        Returns:
            True if check succeeded
        """
        try:
            # Perform health check
            health = await self.monitor.check_all_services()
            
            self.logger.info(
                f"Health check: {health.healthy_count}/{health.total_services} healthy, "
                f"status={health.overall_status.value}"
            )
            
            # Check for overall status change
            prev_status = self.state.get("last_overall_status")
            curr_status = health.overall_status.value
            
            if prev_status != curr_status:
                self.logger.info(f"Status change: {prev_status} → {curr_status}")
                await self._alert_status_change(prev_status, health)
            
            # Check for per-service status changes
            await self._check_service_changes(health)
            
            # Update state
            self.state["last_check"] = datetime.utcnow().isoformat()
            self.state["last_overall_status"] = curr_status
            self.state["service_status"] = {
                check.service_name: check.status.value
                for check in health.checks
            }
            self._save_state()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Check failed: {e}", exc_info=True)
            return False
    
    async def _alert_status_change(self, prev_status: Optional[str], health):
        """Send alert for status change"""
        status_emoji = (
            "✅" if health.overall_status == HealthStatus.HEALTHY
            else "⚠️" if health.overall_status == HealthStatus.UNKNOWN
            else "🚨"
        )
        
        message = f"{status_emoji} <b>Status Update</b>\n\n"
        message += f"<b>Status:</b> {health.overall_status.value.upper()}\n"
        message += f"<b>Health:</b> {health.health_percentage:.1f}%\n"
        message += f"<b>Services:</b> {health.healthy_count}/{health.total_services}\n"
        
        if health.unhealthy_count > 0:
            message += f"\n<b>⚠️ Unhealthy:</b>\n"
            for check in health.checks:
                if check.status == HealthStatus.UNHEALTHY:
                    message += f"  • {check.service_name}: {check.error_message}\n"
        
        message += f"\n<i>{health.checked_at}</i>"
        
        await self.alerter.send_message(message)
    
    async def _check_service_changes(self, health):
        """Check for individual service status changes"""
        prev_service_status = self.state.get("service_status", {})
        
        for check in health.checks:
            prev_status = prev_service_status.get(check.service_name)
            curr_status = check.status.value
            
            # Skip if no previous state
            if prev_status is None:
                continue
            
            # Alert on status transitions
            if prev_status != curr_status:
                if curr_status == HealthStatus.HEALTHY.value:
                    self.logger.info(f"{check.service_name} recovered")
                    await self.alert_manager.alert_service_recovered(check)
                elif prev_status == HealthStatus.HEALTHY.value:
                    self.logger.warning(f"{check.service_name} went down")
                    await self.alert_manager.alert_service_unhealthy(check)


async def main():
    """Main entry point"""
    monitor = get_monitor(base_url=f"http://{settings.DROPLET_IP}")
    cron_monitor = CronMonitor(monitor)
    
    # Parse arguments
    interval = 0  # Default: single run
    daemon = False
    
    for arg in sys.argv[1:]:
        if arg == "--daemon":
            daemon = True
        elif arg.startswith("--interval"):
            try:
                interval = int(arg.split("=")[1])
            except (IndexError, ValueError):
                print("Usage: --interval=SECONDS")
                sys.exit(1)
    
    try:
        if daemon or interval > 0:
            # Continuous monitoring mode
            while True:
                success = await cron_monitor.check_and_alert()
                
                if not success:
                    logger.error("Health check failed")
                    sys.exit(1)
                
                if interval == 0:
                    break
                
                logger.info(f"Next check in {interval}s...")
                await asyncio.sleep(interval)
        else:
            # Single check mode (for cron)
            success = await cron_monitor.check_and_alert()
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("Monitoring stopped")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
