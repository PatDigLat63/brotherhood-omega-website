"""Tests for monitoring and alerts modules"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from core.monitoring import (
    HealthStatus, HealthCheck, SwarmHealth, SwarmMonitor, DiagnosticAnalyzer
)
from core.alerts import AlertLevel, Alert, TelegramAlerter, AlertManager


class TestHealthCheck:
    """Tests for HealthCheck data class"""
    
    def test_health_check_creation(self):
        """Test creating a health check result"""
        check = HealthCheck(
            service_name="omega_patrick",
            status=HealthStatus.HEALTHY,
            port=3005,
            endpoint="/health",
            response_time_ms=45.5
        )
        
        assert check.service_name == "omega_patrick"
        assert check.status == HealthStatus.HEALTHY
        assert check.port == 3005
        assert check.response_time_ms == 45.5
        assert check.error_message is None
        assert check.checked_at is not None
    
    def test_health_check_with_error(self):
        """Test health check with error message"""
        check = HealthCheck(
            service_name="omega_dj",
            status=HealthStatus.UNHEALTHY,
            port=3003,
            endpoint="/health",
            response_time_ms=5000.0,
            error_message="Timeout (unreachable)"
        )
        
        assert check.status == HealthStatus.UNHEALTHY
        assert "Timeout" in check.error_message


class TestSwarmHealth:
    """Tests for SwarmHealth aggregate"""
    
    def test_swarm_health_calculation(self):
        """Test swarm health percentage calculation"""
        checks = [
            HealthCheck("svc1", HealthStatus.HEALTHY, 3005, "/health", 10),
            HealthCheck("svc2", HealthStatus.HEALTHY, 3003, "/health", 15),
            HealthCheck("svc3", HealthStatus.UNHEALTHY, 3006, "/health", 100, "error"),
        ]
        
        health = SwarmHealth(
            total_services=3,
            healthy_count=2,
            unhealthy_count=1,
            unknown_count=0,
            overall_status=HealthStatus.UNHEALTHY,
            checks=checks
        )
        
        assert health.health_percentage == pytest.approx(66.67, rel=0.1)
        assert health.overall_status == HealthStatus.UNHEALTHY


class TestSwarmMonitor:
    """Tests for SwarmMonitor"""
    
    def test_monitor_initialization(self):
        """Test initializing monitor"""
        monitor = SwarmMonitor(base_url="http://localhost", timeout=5)
        
        assert monitor.base_url == "http://localhost"
        assert monitor.timeout == 5
        assert len(monitor.SERVICE_PORTS) > 0
    
    def test_service_ports_defined(self):
        """Test that all expected services are defined"""
        monitor = SwarmMonitor()
        
        expected_services = [
            "omega_patrick",
            "omega_dj",
            "omega_bossman",
            "omega_hashim"
        ]
        
        for service in expected_services:
            assert service in monitor.SERVICE_PORTS
            assert "port" in monitor.SERVICE_PORTS[service]
    
    @pytest.mark.asyncio
    async def test_check_service_health_healthy(self):
        """Test checking a healthy service"""
        monitor = SwarmMonitor()
        
        # Mock the httpx client
        with patch('core.monitoring.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            # Note: This test shows the structure but won't fully work due to async mocking
            # In practice, you'd use pytest-aiohttp or similar for full integration tests


class TestDiagnosticAnalyzer:
    """Tests for DiagnosticAnalyzer"""
    
    def test_diagnose_timeout_failure(self):
        """Test diagnosing timeout failures"""
        check = HealthCheck(
            service_name="omega_patrick",
            status=HealthStatus.UNHEALTHY,
            port=3005,
            endpoint="/health",
            response_time_ms=10000,
            error_message="Timeout (unreachable)"
        )
        
        diag = DiagnosticAnalyzer._diagnose_service(check)
        
        assert "Timeout" in diag["error"]
        assert len(diag["possible_causes"]) > 0
        assert any("listening" in cause.lower() for cause in diag["possible_causes"])
    
    def test_diagnose_connection_refused(self):
        """Test diagnosing connection refused"""
        check = HealthCheck(
            service_name="omega_dj",
            status=HealthStatus.UNHEALTHY,
            port=3003,
            endpoint="/health",
            response_time_ms=0,
            error_message="Connection refused (service not listening)"
        )
        
        diag = DiagnosticAnalyzer._diagnose_service(check)
        
        assert "Connection refused" in diag["error"]
        assert any("started" in cause.lower() for cause in diag["possible_causes"])
    
    def test_diagnose_http_error(self):
        """Test diagnosing HTTP errors"""
        check = HealthCheck(
            service_name="omega_bossman",
            status=HealthStatus.UNHEALTHY,
            port=3006,
            endpoint="/health",
            response_time_ms=200,
            error_message="HTTP 500"
        )
        
        diag = DiagnosticAnalyzer._diagnose_service(check)
        
        assert "HTTP" in diag["error"]
        assert any("endpoint" in step.lower() for step in diag["debugging_steps"])
    
    def test_suggest_fixes(self):
        """Test fix suggestions"""
        check = HealthCheck(
            service_name="omega_patrick",
            status=HealthStatus.UNHEALTHY,
            port=3005,
            endpoint="/health",
            response_time_ms=5000,
            error_message="Timeout"
        )
        
        fixes = DiagnosticAnalyzer._suggest_fixes(check)
        
        assert len(fixes) > 0
        assert any("restart" in fix.lower() for fix in fixes)


class TestAlert:
    """Tests for Alert data class"""
    
    def test_alert_creation(self):
        """Test creating an alert"""
        alert = Alert(
            level=AlertLevel.CRITICAL,
            title="Service Down",
            message="omega_patrick is not responding"
        )
        
        assert alert.level == AlertLevel.CRITICAL
        assert alert.title == "Service Down"
        assert alert.message == "omega_patrick is not responding"
        assert alert.details is None


class TestTelegramAlerter:
    """Tests for TelegramAlerter"""
    
    def test_alerter_initialization(self):
        """Test initializing Telegram alerter"""
        alerter = TelegramAlerter(
            bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            chat_id="987654321"
        )
        
        assert alerter.bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert alerter.chat_id == "987654321"
        assert alerter.enabled is True
    
    def test_alerter_disabled_without_credentials(self):
        """Test alerter is disabled without credentials"""
        alerter = TelegramAlerter(bot_token="", chat_id="")
        
        assert alerter.enabled is False
    
    @pytest.mark.asyncio
    async def test_send_alert_disabled(self):
        """Test sending alert when disabled"""
        alerter = TelegramAlerter(bot_token="", chat_id="")
        alert = Alert(AlertLevel.INFO, "Test", "Test message")
        
        result = await alerter.send_alert(alert)
        
        assert result is False


class TestAlertManager:
    """Tests for AlertManager"""
    
    def test_alert_key_generation(self):
        """Test alert cache key generation"""
        alerter = TelegramAlerter("token", "chat")
        manager = AlertManager(alerter)
        
        key = manager._alert_key("service_down", "omega_patrick")
        
        assert key == "service_down:omega_patrick"
    
    def test_alert_cooldown(self):
        """Test alert cooldown logic"""
        alerter = TelegramAlerter("token", "chat")
        manager = AlertManager(alerter)
        
        key = "test:alert"
        
        # First check should pass
        assert manager._should_alert(key) is True
        
        # Immediate second check should fail (cooldown active)
        assert manager._should_alert(key) is False
        
        # After cooldown, should pass again
        manager._alert_cooldown_seconds = 0
        assert manager._should_alert(key) is True
