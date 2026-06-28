"""
Telegram alerting system for Brotherhood Omega Swarm health events.
Sends notifications for container status changes and critical issues.
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import httpx
from core.config import settings
from core.monitoring import SwarmHealth, HealthStatus, HealthCheck


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "ℹ️"
    WARNING = "⚠️"
    CRITICAL = "🚨"
    SUCCESS = "✅"


@dataclass
class Alert:
    """Single alert message"""
    level: AlertLevel
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None


class TelegramAlerter:
    """Send alerts to Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram alerter
        
        Args:
            bot_token: Telegram bot token (from @BotFather)
            chat_id: Telegram chat/channel ID to send to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send raw message to Telegram
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: "HTML" or "Markdown"
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            self.logger.warning("Telegram alerts disabled - no token/chat_id")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.logger.info(f"Telegram alert sent: {text[:50]}...")
                    return True
                else:
                    self.logger.error(f"Telegram API error: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send formatted alert
        
        Args:
            alert: Alert object
            
        Returns:
            True if sent successfully
        """
        lines = [
            f"{alert.level.value} <b>{alert.title}</b>",
            alert.message
        ]
        
        if alert.details:
            lines.append("\n<i>Details:</i>")
            for key, value in alert.details.items():
                lines.append(f"  • {key}: {value}")
        
        text = "\n".join(lines)
        return await self.send_message(text)
    
    async def send_swarm_health_report(self, health: SwarmHealth) -> bool:
        """
        Send swarm health status report
        
        Args:
            health: SwarmHealth result
            
        Returns:
            True if sent successfully
        """
        status_emoji = (
            "✅" if health.overall_status == HealthStatus.HEALTHY
            else "⚠️" if health.overall_status == HealthStatus.UNKNOWN
            else "🚨"
        )
        
        lines = [
            f"{status_emoji} <b>Swarm Health Report</b>",
            "",
            f"<b>Status:</b> {health.overall_status.value.upper()}",
            f"<b>Health:</b> {health.health_percentage:.1f}%",
            f"<b>Services:</b> {health.healthy_count}/{health.total_services} healthy"
        ]
        
        if health.unhealthy_count > 0:
            lines.append(f"<b>⚠️ Unhealthy:</b> {health.unhealthy_count}")
            for check in health.checks:
                if check.status == HealthStatus.UNHEALTHY:
                    lines.append(f"  • {check.service_name}: {check.error_message}")
        
        if health.unknown_count > 0:
            lines.append(f"<b>❓ Unknown:</b> {health.unknown_count}")
        
        lines.append(f"\n<i>Updated:</i> {health.checked_at}")
        
        text = "\n".join(lines)
        return await self.send_message(text)
    
    async def send_service_down_alert(self, check: HealthCheck) -> bool:
        """
        Send alert for service going down
        
        Args:
            check: Failed health check
            
        Returns:
            True if sent successfully
        """
        alert = Alert(
            level=AlertLevel.CRITICAL,
            title=f"Service Down: {check.service_name}",
            message=f"Port {check.port} is not responding to health checks.",
            details={
                "Service": check.service_name,
                "Port": check.port,
                "Error": check.error_message,
                "Response Time": f"{check.response_time_ms:.0f}ms",
                "Endpoint": check.endpoint
            }
        )
        return await self.send_alert(alert)
    
    async def send_service_recovered_alert(self, check: HealthCheck) -> bool:
        """
        Send alert for service recovery
        
        Args:
            check: Recovered health check
            
        Returns:
            True if sent successfully
        """
        alert = Alert(
            level=AlertLevel.SUCCESS,
            title=f"Service Recovered: {check.service_name}",
            message=f"Port {check.port} is now responding normally.",
            details={
                "Service": check.service_name,
                "Port": check.port,
                "Response Time": f"{check.response_time_ms:.0f}ms",
                "Status": "HEALTHY"
            }
        )
        return await self.send_alert(alert)
    
    async def send_circuit_breaker_alert(
        self,
        reason: str,
        metrics: Dict[str, Any]
    ) -> bool:
        """
        Send circuit breaker trip alert
        
        Args:
            reason: Why circuit breaker tripped
            metrics: Breaker metrics
            
        Returns:
            True if sent successfully
        """
        alert = Alert(
            level=AlertLevel.CRITICAL,
            title="🚨 Circuit Breaker Tripped",
            message=f"Trading halted - {reason}",
            details=metrics
        )
        return await self.send_alert(alert)


class AlertManager:
    """Manage alerts and prevent alert flooding"""
    
    def __init__(self, alerter: TelegramAlerter):
        """
        Initialize alert manager
        
        Args:
            alerter: TelegramAlerter instance
        """
        self.alerter = alerter
        self.logger = logging.getLogger(__name__)
        self._last_alerts: Dict[str, float] = {}  # Alert key -> last sent time
        self._alert_cooldown_seconds = 300  # 5 minutes between same alert
    
    def _alert_key(self, alert_type: str, service_name: str = "") -> str:
        """Generate alert cache key"""
        return f"{alert_type}:{service_name}"
    
    def _should_alert(self, key: str) -> bool:
        """Check if enough time has passed since last alert of this type"""
        import time
        now = time.time()
        last_time = self._last_alerts.get(key, 0)
        
        if now - last_time >= self._alert_cooldown_seconds:
            self._last_alerts[key] = now
            return True
        
        return False
    
    async def alert_service_unhealthy(self, check: HealthCheck) -> bool:
        """
        Alert if service is unhealthy (with cooldown)
        
        Returns:
            True if alert was sent
        """
        key = self._alert_key("service_down", check.service_name)
        
        if self._should_alert(key):
            return await self.alerter.send_service_down_alert(check)
        
        return False
    
    async def alert_service_recovered(self, check: HealthCheck) -> bool:
        """
        Alert when service recovers
        
        Returns:
            True if alert was sent
        """
        key = self._alert_key("service_recovered", check.service_name)
        
        if self._should_alert(key):
            return await self.alerter.send_service_recovered_alert(check)
        
        return False
    
    async def alert_swarm_unhealthy(self, health: SwarmHealth) -> bool:
        """
        Alert if swarm is unhealthy overall
        
        Returns:
            True if alert was sent
        """
        key = self._alert_key("swarm_health")
        
        if health.overall_status != HealthStatus.HEALTHY:
            if self._should_alert(key):
                return await self.alerter.send_swarm_health_report(health)
        
        return False


def get_alerter() -> TelegramAlerter:
    """Get Telegram alerter configured from settings"""
    return TelegramAlerter(
        bot_token=settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
        chat_id=settings.TELEGRAM_CHAT_ID
    )


def get_alert_manager() -> AlertManager:
    """Get alert manager instance"""
    return AlertManager(get_alerter())
