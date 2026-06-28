"""Basic verification tests for Brotherhood Omega Dynasty."""

def test_imports():
    """Verify all core modules can be imported."""
    from core.config import Settings
    from core.security import Vault
    assert True

def test_config_validation(monkeypatch):
    """Verify config loads with test environment."""
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", "dGVzdC1rZXktZm9yLWNpLW9ubHktMzJieXRlcw==")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-for-ci-only-64-chars-long")
    monkeypatch.setenv("HELIUS_API_KEY", "test")
    monkeypatch.setenv("BIRDEYE_API_KEY", "test")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_URL", "https://test.com")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "test")
    monkeypatch.setenv("GOD_USER_IDS", "123")
    monkeypatch.setenv("A2A_PATRICK_SEED", "0"*64)
    monkeypatch.setenv("A2A_HASHIM_SEED", "0"*64)
    monkeypatch.setenv("A2A_BOSSMAN_SEED", "0"*64)
    monkeypatch.setenv("A2A_DJ_SEED", "0"*64)
    monkeypatch.setenv("AGENT_PATRICK_API_KEY", "test")
    monkeypatch.setenv("AGENT_HASHIM_API_KEY", "test")
    monkeypatch.setenv("AGENT_BOSSMAN_API_KEY", "test")
    monkeypatch.setenv("AGENT_DJ_API_KEY", "test")
    
    from core.config import Settings
    settings = Settings()
    assert settings.HELIUS_API_KEY.get_secret_value() == "test"
    assert settings.DROPLET_IP == "206.189.118.255"
