"""Configuration with Pydantic settings"""
import os
from typing import Optional, List
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DROPLET_IP: str = "206.189.118.255"
    MASTER_ENCRYPTION_KEY: SecretStr = Field(default="test-key")
    JWT_SECRET_KEY: SecretStr = Field(default="test-jwt-secret")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    DATABASE_URL: str = "postgresql+asyncpg://swarm:swarm@localhost:5432/brotherhood"
    REDIS_URL: str = "redis://localhost:6379/0"
    HELIUS_API_KEY: SecretStr = Field(default="test-helius-key")
    HELIUS_RPC_URL: str = "https://mainnet.helius-rpc.com"
    JUPITER_API_URL: str = "https://quote-api.jup.ag/v6"
    JUPITER_PRIORITY_FEE_MICROLAMPORTS: int = 50000
    BIRDEYE_API_KEY: SecretStr = Field(default="test-birdeye-key")
    BIRDEYE_BASE_URL: str = "https://public-api.birdeye.so"
    RUGCHECK_API_URL: str = "https://api.rugcheck.xyz/v1"
    JITO_API_URL: str = "https://mainnet.block-engine.jito.wtf/api/v1"
    JITO_TIP_LAMPORTS: int = 1000000
    USE_JITO_BUNDLES: bool = True
    ETH_RPC_URL: str = "https://eth-mainnet.g.alchemy.com/v2/"
    BSC_RPC_URL: str = "https://bsc-dataseed.binance.org/"
    POLYGON_RPC_URL: str = "https://polygon-rpc.com/"
    BTC_API_URL: str = "https://mempool.space/api"
    HEDERA_MIRROR_NODE: str = "https://mainnet-public.mirrornode.hedera.com"
    LIFI_API_URL: str = "https://li.quest/v1"
    TELEGRAM_BOT_TOKEN: SecretStr = Field(default="test-token")
    TELEGRAM_CHAT_ID: str = "123456789"
    TELEGRAM_WEBHOOK_URL: str = "https://test.example.com"
    TELEGRAM_WEBHOOK_SECRET: str = "test-secret"
    GOD_USER_IDS: str = "123456789"
    A2A_PATRICK_SEED: SecretStr = Field(default="0"*64)
    A2A_HASHIM_SEED: SecretStr = Field(default="0"*64)
    A2A_BOSSMAN_SEED: SecretStr = Field(default="0"*64)
    A2A_DJ_SEED: SecretStr = Field(default="0"*64)
    AGENT_PATRICK_API_KEY: SecretStr = Field(default="test-patrick-key")
    AGENT_HASHIM_API_KEY: SecretStr = Field(default="test-hashim-key")
    AGENT_BOSSMAN_API_KEY: SecretStr = Field(default="test-bossman-key")
    AGENT_DJ_API_KEY: SecretStr = Field(default="test-dj-key")
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    DEFAULT_SLIPPAGE_BPS: int = 150
    MAX_SLIPPAGE_BPS: int = 300
    SIMULATE_BEFORE_EXECUTE: bool = True
    MIN_SOL_BALANCE: float = 0.05
    MAX_DAILY_TRADES_PER_AGENT: int = 50
    GLOBAL_EMERGENCY_STOP: bool = False
    YOLO_MULTIPLIER: float = 75.0
    MAX_DRAWDOWN_PCT: float = 18.0
    COMPOUND_RATIO: float = 92.0
    RESERVE_RATIO: float = 8.0
    COMPOUND_INTERVAL: int = 3600
    TRADE_INTERVAL: int = 30
    SCAN_INTERVAL: int = 60
    CROSS_CHAIN_SCAN_INTERVAL: int = 3600
    DUST_THRESHOLD_USD: float = 1.0
    ARB_MIN_PROFIT_PCT: float = 2.0
    ARB_MAX_BRIDGE_TIME_MIN: int = 30
    DEAD_POSITION_THRESHOLD_DAYS: int = 30
    
    @property
    def god_user_ids_list(self) -> List[int]:
        return [int(x.strip()) for x in self.GOD_USER_IDS.split(",")]
    
    @property
    def helius_rpc_url(self) -> str:
        return f"{self.HELIUS_RPC_URL}/?api-key={self.HELIUS_API_KEY.get_secret_value()}"
    
    @property
    def birdeye_headers(self) -> dict:
        return {"X-API-KEY": self.BIRDEYE_API_KEY.get_secret_value()}

settings = Settings()
