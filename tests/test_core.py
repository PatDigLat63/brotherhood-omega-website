"""Basic verification tests for Brotherhood Omega Dynasty."""

def test_imports():
    """Verify all core modules can be imported."""
    from core.config import Settings
    from core.security import Vault
    assert True

def test_config_validation():
    """Verify config loads with test environment."""
    import os
    os.environ.setdefault("MASTER_ENCRYPTION_KEY", "dGVzdC1rZXktZm9yLWNpLW9ubHktMzJieXRlcw==")
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-ci-only-64-chars-long")
    os.environ.setdefault("HELIUS_API_KEY", "test")
    os.environ.setdefault("BIRDEYE_API_KEY", "test")
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123:test")
    os.environ.setdefault("TELEGRAM_CHAT_ID", "123")
    os.environ.setdefault("TELEGRAM_WEBHOOK_URL", "https://test.com")
    os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "test")
    os.environ.setdefault("GOD_USER_IDS", "123")
    os.environ.setdefault("A2A_PATRICK_SEED", "0"*64)
    os.environ.setdefault("A2A_HASHIM_SEED", "0"*64)
    os.environ.setdefault("A2A_BOSSMAN_SEED", "0"*64)
    os.environ.setdefault("A2A_DJ_SEED", "0"*64)
    os.environ.setdefault("AGENT_PATRICK_API_KEY", "test")
    os.environ.setdefault("AGENT_HASHIM_API_KEY", "test")
    os.environ.setdefault("AGENT_BOSSMAN_API_KEY", "test")
    os.environ.setdefault("AGENT_DJ_API_KEY", "test")
    
    from core.config import Settings
    settings = Settings()
    assert settings.HELIUS_API_KEY.get_secret_value() == "test"
    assert settings.DROPLET_IP == "206.189.118.255"
