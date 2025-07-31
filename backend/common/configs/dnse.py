import random
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from backend.common.consts import DNSEConsts


@dataclass
class TradingAPIConfig:
    base_url: str = DNSEConsts.BASE_URL
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    concurrent_limit: int = 10


@dataclass
class AuthConfig(TradingAPIConfig):
    token_expiry_hours: int = 7


@dataclass
class MarketDataConfig:
    broker: str = DNSEConsts.BROKER
    port: int = 443
    client_id: str = f"python-json-mqtt-ws-sub-{random.randint(0, 1000)}"
    first_reconnect_delay: int = 1
    reconnect_rate: int = 2
    max_reconnect_count: int = 12
    max_reconnect_delay: int = 60
