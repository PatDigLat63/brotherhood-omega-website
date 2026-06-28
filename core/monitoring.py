"""
Health check and container monitoring for Brotherhood Omega Swarm.
Diagnoses unhealthy containers and collects telemetry.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import httpx


class HealthStatus(str, Enum):
    """Container health status enum"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"


@dataclass
class HealthCheck:
    """Individual health check result"""
    service_name: str
    status: HealthStatus
    port: int
    endpoint: str
    response_time_ms: float
    error_message: Optional[str] = None
    checked_at: str = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow().isoformat()


@dataclass
class SwarmHealth:
    """Overall swarm health status"""
    total_services: int
    healthy_count: int
    unhealthy_count: int
    unknown_count: int
    overall_status: HealthStatus
    checks: List[HealthCheck]
    checked_at: str = None
    
    def __post_init__(self):
        if self.checked_at is None:
            self.checked_at = datetime.utcnow().isoformat()
    
    @property
    def health_percentage(self) -> float:
        """Calculate health percentage"""
        if self.total_services == 0:
            return 0.0
        return (self.healthy_count / self.total_services) * 100


class SwarmMonitor:
    """Monitor container health across the swarm"""
    
    # Standard service ports
    SERVICE_PORTS = {
        "omega_patrick": {"port": 3005, "name": "Scanner Agent"},
        "omega_dj": {"port": 3003, "name": "Executor Agent"},
        "omega_bossman": {"port": 3006, "name": "Risk Guardian"},
        "omega_hashim": {"port": 3004, "name": "Compounder"},
        "omega_hustle_bridge": {"port": 3001, "name": "Bridge Service"},
        "omega_oracle_engine": {"port": 3002, "name": "Oracle"},
        "omega_dashboard": {"port": 8082, "name": "Dashboard"},
        "omega_agentbus": {"port": 8081, "name": "AgentBus"},
        "omega_telegram_bot": {"port": 8083, "name": "Telegram Bot"},
    }
    
    def __init__(self, base_url: str = "http://206.189.118.255", timeout: int = 10):
        """
        Initialize swarm monitor
        
        Args:
            base_url: Base URL for health checks (e.g. http://droplet-ip)
            timeout: HTTP timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.health_history: Dict[str, List[HealthCheck]] = {}
    
    async def check_service_health(
        self,
        service_name: str,
        port: int,
        endpoint: str = "/health"
    ) -> HealthCheck:
        """
        Check health of a single service
        
        Args:
            service_name: Service identifier
            port: Service port
            endpoint: Health check endpoint
            
        Returns:
            HealthCheck result
        """
        url = f"{self.base_url}:{port}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start = datetime.utcnow()
                response = await client.get(url)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                
                # Consider 2xx as healthy
                if 200 <= response.status_code < 300:
                    status = HealthStatus.HEALTHY
                    error_msg = None
                else:
                    status = HealthStatus.UNHEALTHY
                    error_msg = f"HTTP {response.status_code}"
                    
        except asyncio.TimeoutError:
            status = HealthStatus.UNHEALTHY
            error_msg = "Timeout (unreachable)"
            elapsed = self.timeout * 1000
        except httpx.ConnectError:
            status = HealthStatus.UNHEALTHY
            error_msg = "Connection refused (service not listening)"
            elapsed = 0
        except Exception as e:
            status = HealthStatus.UNKNOWN
            error_msg = str(e)
            elapsed = 0
        
        check = HealthCheck(
            service_name=service_name,
            status=status,
            port=port,
            endpoint=endpoint,
            response_time_ms=elapsed,
            error_message=error_msg
        )
        
        # Track history
        if service_name not in self.health_history:
            self.health_history[service_name] = []
        self.health_history[service_name].append(check)
        
        # Keep only last 100 checks per service
        if len(self.health_history[service_name]) > 100:
            self.health_history[service_name] = self.health_history[service_name][-100:]
        
        return check
    
    async def check_all_services(self) -> SwarmHealth:
        """
        Check health of all known services
        
        Returns:
            SwarmHealth aggregate result
        """
        checks = []
        tasks = []
        
        for service_name, config in self.SERVICE_PORTS.items():
            task = self.check_service_health(
                service_name=service_name,
                port=config["port"],
                endpoint="/health"
            )
            tasks.append(task)
        
        checks = await asyncio.gather(*tasks)
        
        # Calculate aggregate health
        healthy_count = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
        unhealthy_count = sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY)
        unknown_count = sum(1 for c in checks if c.status == HealthStatus.UNKNOWN)
        
        # Determine overall status
        if unhealthy_count > 0:
            overall = HealthStatus.UNHEALTHY
        elif unknown_count > 0:
            overall = HealthStatus.UNKNOWN
        else:
            overall = HealthStatus.HEALTHY
        
        return SwarmHealth(
            total_services=len(checks),
            healthy_count=healthy_count,
            unhealthy_count=unhealthy_count,
            unknown_count=unknown_count,
            overall_status=overall,
            checks=sorted(checks, key=lambda c: c.service_name)
        )
    
    def get_trend(self, service_name: str, window_seconds: int = 300) -> Dict[str, Any]:
        """
        Get health trend for a service over time window
        
        Args:
            service_name: Service to analyze
            window_seconds: Time window to analyze
            
        Returns:
            Trend analysis with uptime percentage
        """
        if service_name not in self.health_history:
            return {"error": "No history for service"}
        
        history = self.health_history[service_name]
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        recent = [
            c for c in history
            if datetime.fromisoformat(c.checked_at) > cutoff
        ]
        
        if not recent:
            return {"samples": 0, "uptime_pct": 0}
        
        healthy = sum(1 for c in recent if c.status == HealthStatus.HEALTHY)
        uptime_pct = (healthy / len(recent)) * 100
        
        avg_response_time = sum(c.response_time_ms for c in recent) / len(recent)
        
        return {
            "samples": len(recent),
            "uptime_pct": uptime_pct,
            "avg_response_time_ms": avg_response_time,
            "window_seconds": window_seconds
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize monitor state"""
        return {
            "base_url": self.base_url,
            "health_history": {
                service: [asdict(check) for check in checks]
                for service, checks in self.health_history.items()
            }
        }


class DiagnosticAnalyzer:
    """Analyze health check failures to diagnose root causes"""
    
    @staticmethod
    def diagnose_failures(swarm_health: SwarmHealth) -> Dict[str, Any]:
        """
        Analyze unhealthy services and suggest root causes
        
        Args:
            swarm_health: SwarmHealth result
            
        Returns:
            Diagnostic report with possible issues and fixes
        """
        diagnostics = {
            "summary": [],
            "issues_by_service": {},
            "common_issues": [],
            "recommended_fixes": []
        }
        
        for check in swarm_health.checks:
            if check.status == HealthStatus.UNHEALTHY:
                service_diag = DiagnosticAnalyzer._diagnose_service(check)
                diagnostics["issues_by_service"][check.service_name] = service_diag
        
        # Identify common patterns
        if swarm_health.unhealthy_count > 5:
            diagnostics["common_issues"].append(
                "Multiple services unhealthy - likely system-wide issue "
                "(API key auth failure, database connectivity, DNS resolution)"
            )
        
        # Generate recommended fixes
        for check in swarm_health.checks:
            if check.status == HealthStatus.UNHEALTHY:
                fixes = DiagnosticAnalyzer._suggest_fixes(check)
                for fix in fixes:
                    if fix not in diagnostics["recommended_fixes"]:
                        diagnostics["recommended_fixes"].append(fix)
        
        return diagnostics
    
    @staticmethod
    def _diagnose_service(check: HealthCheck) -> Dict[str, str]:
        """Diagnose specific service failure"""
        diag = {
            "error": check.error_message or "Unknown error",
            "possible_causes": [],
            "debugging_steps": []
        }
        
        if "Timeout" in check.error_message or "unreachable" in check.error_message:
            diag["possible_causes"] = [
                "Service not listening on port",
                "Service crashed or failed to start",
                "Network connectivity issue",
                "Firewall blocking traffic"
            ]
            diag["debugging_steps"] = [
                f"docker logs {check.service_name} --tail 50",
                f"netstat -tlnp | grep {check.port}",
                "docker inspect {container_id} | grep -A 5 Health"
            ]
        
        elif "Connection refused" in check.error_message:
            diag["possible_causes"] = [
                "Service hasn't started yet (startup delay)",
                "Service binding to wrong port",
                "Service crashed immediately after start"
            ]
            diag["debugging_steps"] = [
                f"docker logs {check.service_name} --tail 100",
                "docker ps | grep {check.service_name}"
            ]
        
        elif "HTTP" in check.error_message:
            diag["possible_causes"] = [
                "Health check endpoint returns error status",
                "Service not ready yet (startup initialization)",
                "Authentication/Authorization failure",
                "Configuration/environment variable missing"
            ]
            diag["debugging_steps"] = [
                f"curl -v http://206.189.118.255:{check.port}/health",
                f"docker logs {check.service_name} | grep -i error"
            ]
        
        return diag
    
    @staticmethod
    def _suggest_fixes(check: HealthCheck) -> List[str]:
        """Suggest fixes for unhealthy service"""
        fixes = []
        
        # Universal fixes
        fixes.append(f"Restart container: docker restart {check.service_name}")
        
        if "Timeout" in check.error_message or "Connection refused" in check.error_message:
            fixes.append(f"Check logs: docker logs {check.service_name} --tail 100")
            fixes.append("Verify .env file exists and has correct API keys")
            fixes.append("Increase health check timeout in docker-compose.yml")
        
        elif "HTTP" in check.error_message:
            fixes.append(f"Check endpoint: curl http://206.189.118.255:{check.port}/health")
            fixes.append("Verify environment variables are loaded")
        
        # General Docker fixes
        fixes.append("Restart docker daemon: sudo systemctl restart docker")
        fixes.append("Check system resources: docker stats --no-stream")
        fixes.append("Prune unused images: docker system prune -f")
        
        return fixes


# Singleton instance
_monitor_instance: Optional[SwarmMonitor] = None


def get_monitor(base_url: str = "http://206.189.118.255") -> SwarmMonitor:
    """Get or create monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SwarmMonitor(base_url=base_url)
    return _monitor_instance
