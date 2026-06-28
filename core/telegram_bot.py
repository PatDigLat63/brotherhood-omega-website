"""
Telegram Bot command handlers for Brotherhood Omega Swarm monitoring.

Implements interactive commands:
  /swarm - Overall swarm health and status
  /agent NAME - Specific agent status and logs
  /metrics - Trading metrics, uptime, drawdown
  /alerts on/off - Enable/disable monitoring alerts
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

from core.monitoring import SwarmMonitor, HealthStatus, get_monitor
from core.alerts import get_alerter, TelegramAlerter
from core.config import settings


logger = logging.getLogger(__name__)


@dataclass
class CommandContext:
    """Context for command execution"""
    command: str
    args: List[str]
    user_id: str
    chat_id: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class TelegramBotCommands:
    """Handle Telegram bot commands for swarm monitoring"""
    
    def __init__(self, monitor: SwarmMonitor = None, alerter: TelegramAlerter = None):
        """
        Initialize command handler
        
        Args:
            monitor: SwarmMonitor instance (uses default if None)
            alerter: TelegramAlerter instance (uses default if None)
        """
        self.monitor = monitor or get_monitor()
        self.alerter = alerter or get_alerter()
        self.logger = logging.getLogger(__name__)
        self._alerts_enabled: Dict[str, bool] = {}  # user_id -> enabled
    
    async def handle_command(self, context: CommandContext) -> bool:
        """
        Handle incoming command
        
        Args:
            context: Command context
            
        Returns:
            True if command handled successfully
        """
        handler_map = {
            "swarm": self._handle_swarm,
            "agent": self._handle_agent,
            "metrics": self._handle_metrics,
            "alerts": self._handle_alerts,
            "health": self._handle_swarm,  # Alias for /swarm
            "status": self._handle_swarm,  # Alias for /swarm
            "help": self._handle_help,
        }
        
        handler = handler_map.get(context.command)
        if not handler:
            await self._send_response(
                context.chat_id,
                f"❌ Unknown command: /{context.command}\n"
                f"Use /help for available commands"
            )
            return False
        
        try:
            result = await handler(context)
            return result
        except Exception as e:
            self.logger.error(f"Error handling {context.command}: {e}", exc_info=True)
            await self._send_response(
                context.chat_id,
                f"❌ Error executing command: {str(e)[:100]}"
            )
            return False
    
    async def _handle_swarm(self, context: CommandContext) -> bool:
        """Handle /swarm command - show overall swarm health"""
        health = await self.monitor.check_all_services()
        
        status_emoji = (
            "✅" if health.overall_status == HealthStatus.HEALTHY
            else "⚠️" if health.overall_status == HealthStatus.UNKNOWN
            else "🚨"
        )
        
        lines = [
            f"<b>{status_emoji} BROTHERHOOD OMEGA SWARM STATUS</b>",
            "",
            f"<b>Overall Status:</b> {health.overall_status.value.upper()}",
            f"<b>Health Score:</b> {health.health_percentage:.1f}%",
            f"<b>Services:</b> {health.healthy_count}✅ / {health.total_services} total",
        ]
        
        if health.unhealthy_count > 0:
            lines.append(f"\n<b>⚠️ Unhealthy Services ({health.unhealthy_count}):</b>")
            for check in health.checks:
                if check.status == HealthStatus.UNHEALTHY:
                    lines.append(f"  • <code>{check.service_name}</code>: {check.error_message}")
        
        if health.unknown_count > 0:
            lines.append(f"\n<b>❓ Unknown Status ({health.unknown_count}):</b>")
            for check in health.checks:
                if check.status == HealthStatus.UNKNOWN:
                    lines.append(f"  • <code>{check.service_name}</code>")
        
        lines.append(f"\n<i>Last updated:</i> {health.checked_at}")
        lines.append("\n<i>Use /agent NAME for detailed info</i>")
        
        text = "\n".join(lines)
        return await self._send_response(context.chat_id, text)
    
    async def _handle_agent(self, context: CommandContext) -> bool:
        """Handle /agent command - show specific agent status"""
        if not context.args:
            await self._send_response(
                context.chat_id,
                "❌ Usage: /agent NAME\n"
                "Example: /agent patrick\n"
                "Available agents: patrick, dj, bossman, hashim, "
                "hustle_bridge, oracle_engine, dashboard, agentbus"
            )
            return False
        
        agent_name = f"omega_{context.args[0].lower()}"
        
        # Check if service exists
        if agent_name not in self.monitor.SERVICE_PORTS:
            available = ", ".join(
                s.replace("omega_", "") for s in self.monitor.SERVICE_PORTS.keys()
            )
            await self._send_response(
                context.chat_id,
                f"❌ Unknown agent: {context.args[0]}\n"
                f"Available: {available}"
            )
            return False
        
        config = self.monitor.SERVICE_PORTS[agent_name]
        health = await self.monitor.check_all_services()
        
        # Find this service's check
        check = next((c for c in health.checks if c.service_name == agent_name), None)
        if not check:
            await self._send_response(
                context.chat_id,
                f"❌ Could not retrieve status for {agent_name}"
            )
            return False
        
        status_icon = (
            "✅" if check.status == HealthStatus.HEALTHY
            else "❌" if check.status == HealthStatus.UNHEALTHY
            else "❓"
        )
        
        lines = [
            f"<b>{status_icon} AGENT STATUS: {agent_name}</b>",
            "",
            f"<b>Status:</b> {check.status.value.upper()}",
            f"<b>Port:</b> {check.port}",
            f"<b>Endpoint:</b> {check.endpoint}",
            f"<b>Response Time:</b> {check.response_time_ms:.0f}ms",
        ]
        
        if check.error_message:
            lines.append(f"<b>Error:</b> {check.error_message}")
        
        # Get history if available
        if agent_name in self.monitor.health_history:
            history = self.monitor.health_history[agent_name]
            if history:
                lines.append("\n<b>Recent Status:</b>")
                for check_hist in history[-5:]:
                    status_icon = (
                        "✅" if check_hist.status == HealthStatus.HEALTHY else "❌"
                    )
                    lines.append(
                        f"  {status_icon} {check_hist.checked_at[-8:]}: "
                        f"{check_hist.response_time_ms:.0f}ms"
                    )
                
                # Calculate uptime
                healthy_count = sum(
                    1 for c in history if c.status == HealthStatus.HEALTHY
                )
                uptime_pct = (healthy_count / len(history)) * 100 if history else 0
                lines.append(f"\n<b>Uptime:</b> {uptime_pct:.1f}% (last {len(history)} checks)")
        
        text = "\n".join(lines)
        return await self._send_response(context.chat_id, text)
    
    async def _handle_metrics(self, context: CommandContext) -> bool:
        """Handle /metrics command - show trading metrics"""
        lines = [
            "<b>📊 TRADING METRICS</b>",
            "",
        ]
        
        # Get swarm health
        health = await self.monitor.check_all_services()
        
        lines.append("<b>Swarm Status:</b>")
        lines.append(f"  • Health: {health.health_percentage:.1f}%")
        lines.append(f"  • Services Online: {health.healthy_count}/{health.total_services}")
        lines.append(f"  • Status: {health.overall_status.value.upper()}")
        
        # Trading metrics (from settings/config)
        lines.append("\n<b>Configuration:</b>")
        lines.append(f"  • Max Daily Trades: {settings.MAX_DAILY_TRADES_PER_AGENT}")
        lines.append(f"  • Max Drawdown: {settings.MAX_DRAWDOWN_PCT}%")
        lines.append(f"  • Max Slippage: {settings.MAX_SLIPPAGE_BPS} BPS")
        lines.append(f"  • Compound Ratio: {settings.COMPOUND_RATIO}%")
        lines.append(f"  • Reserve Ratio: {settings.RESERVE_RATIO}%")
        
        # Circuit breaker status
        lines.append("\n<b>Safety:</b>")
        status = "🚨 ACTIVE" if settings.GLOBAL_EMERGENCY_STOP else "✅ Normal"
        lines.append(f"  • Circuit Breaker: {status}")
        lines.append(f"  • Min SOL Balance: {settings.MIN_SOL_BALANCE}")
        
        lines.append(f"\n<i>Updated:</i> {datetime.utcnow().isoformat()}")
        
        text = "\n".join(lines)
        return await self._send_response(context.chat_id, text)
    
    async def _handle_alerts(self, context: CommandContext) -> bool:
        """Handle /alerts command - enable/disable monitoring"""
        if not context.args:
            state = "enabled" if self._alerts_enabled.get(context.user_id, True) else "disabled"
            await self._send_response(
                context.chat_id,
                f"ℹ️ Alerts are currently {state}\n"
                f"Use: /alerts on  (enable)\n"
                f"Use: /alerts off (disable)"
            )
            return True
        
        action = context.args[0].lower()
        
        if action == "on":
            self._alerts_enabled[context.user_id] = True
            message = "✅ Monitoring alerts enabled"
        elif action == "off":
            self._alerts_enabled[context.user_id] = False
            message = "⏸️ Monitoring alerts disabled"
        else:
            message = f"❌ Unknown action: {action}\nUse: on or off"
        
        return await self._send_response(context.chat_id, message)
    
    async def _handle_help(self, context: CommandContext) -> bool:
        """Handle /help command"""
        lines = [
            "<b>🔱 BROTHERHOOD OMEGA MONITORING COMMANDS</b>",
            "",
            "<b>/swarm</b> - Overall swarm health and status",
            "  Shows: Health %, service count, unhealthy agents",
            "",
            "<b>/agent NAME</b> - Specific agent detailed status",
            "  Example: <code>/agent patrick</code>",
            "  Shows: Status, port, response time, uptime %",
            "",
            "<b>/metrics</b> - Trading metrics and configuration",
            "  Shows: Swarm health, trade limits, drawdown, safety status",
            "",
            "<b>/alerts on|off</b> - Enable/disable monitoring alerts",
            "  Default: Alerts enabled",
            "",
            "<b>/help</b> - Show this message",
            "",
            "<i>Available agents:</i>",
            "  patrick, dj, bossman, hashim, hustle_bridge,",
            "  oracle_engine, dashboard, agentbus",
        ]
        
        text = "\n".join(lines)
        return await self._send_response(context.chat_id, text)
    
    async def _send_response(self, chat_id: str, text: str) -> bool:
        """Send response to chat"""
        try:
            return await self.alerter.send_message(text, parse_mode="HTML")
        except Exception as e:
            self.logger.error(f"Failed to send response: {e}")
            return False
    
    def is_alerts_enabled(self, user_id: str) -> bool:
        """Check if alerts are enabled for user"""
        return self._alerts_enabled.get(user_id, True)


# Singleton instance
_commands_instance: Optional[TelegramBotCommands] = None


def get_telegram_commands() -> TelegramBotCommands:
    """Get or create Telegram commands handler"""
    global _commands_instance
    if _commands_instance is None:
        _commands_instance = TelegramBotCommands()
    return _commands_instance
