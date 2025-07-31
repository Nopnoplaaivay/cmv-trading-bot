import asyncio
import aiohttp
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, Protocol
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import aiofiles
import os
from contextlib import asynccontextmanager

# Optional imports for different storage backends
try:
    import aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

try:
    import asyncpg
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    asyncpg = None

from src.utils.logger import LOGGER


class OTPType(Enum):
    SMART = "smart"
    EMAIL = "email"


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


@dataclass
class TokenData:
    """Token data structure"""
    token: str
    trading_token: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    username: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        if not self.expires_at:
            return True
        return datetime.now() < self.expires_at
    
    def time_remaining(self) -> Optional[timedelta]:
        """Get remaining time for token"""
        if not self.expires_at:
            return None
        remaining = self.expires_at - datetime.now()
        return remaining if remaining > timedelta(0) else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenData':
        """Create TokenData from dictionary"""
        # Convert ISO format strings back to datetime objects
        for key in ['created_at', 'expires_at']:
            if key in data and data[key]:
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


class TokenStorage(ABC):
    @abstractmethod
    async def save_token(self, username: str, token_data: TokenData) -> None:
        """Save token data"""
        pass
    
    @abstractmethod
    async def load_token(self, username: str) -> Optional[TokenData]:
        """Load token data"""
        pass
    
    @abstractmethod
    async def delete_token(self, username: str) -> None:
        """Delete token data"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass



class RedisTokenStorage(TokenStorage):
    """Redis-based token storage"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "dnse_token:"):
        if not REDIS_AVAILABLE:
            raise ImportError("aioredis is required for Redis storage")
        
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis: Optional[aioredis.Redis] = None
    
    async def _get_redis(self) -> aioredis.Redis:
        """Get Redis connection"""
        if self.redis is None:
            self.redis = aioredis.from_url(self.redis_url)
        return self.redis
    
    def _get_key(self, username: str) -> str:
        """Get Redis key for username"""
        return f"{self.key_prefix}{username}"
    
    async def save_token(self, username: str, token_data: TokenData) -> None:
        """Save token to Redis"""
        try:
            redis = await self._get_redis()
            key = self._get_key(username)
            data = json.dumps(token_data.to_dict())
            
            # Set expiration if token has expiry time
            if token_data.expires_at:
                expire_seconds = int((token_data.expires_at - datetime.now()).total_seconds())
                await redis.setex(key, expire_seconds, data)
            else:
                await redis.set(key, data)
            
            LOGGER.info(f"Token saved to Redis for user: {username}")
        except Exception as e:
            LOGGER.error(f"Failed to save token to Redis: {e}")
            raise
    
    async def load_token(self, username: str) -> Optional[TokenData]:
        """Load token from Redis"""
        try:
            redis = await self._get_redis()
            key = self._get_key(username)
            data = await redis.get(key)
            
            if data:
                token_dict = json.loads(data)
                return TokenData.from_dict(token_dict)
            return None
        except Exception as e:
            LOGGER.error(f"Failed to load token from Redis: {e}")
            return None
    
    async def delete_token(self, username: str) -> None:
        """Delete token from Redis"""
        try:
            redis = await self._get_redis()
            key = self._get_key(username)
            await redis.delete(key)
        except Exception as e:
            LOGGER.error(f"Failed to delete token from Redis: {e}")
    
    async def cleanup(self) -> None:
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()


class PostgresTokenStorage(TokenStorage):
    """PostgreSQL-based token storage"""
    
    def __init__(self, dsn: str, table_name: str = "dnse_tokens"):
        if not POSTGRES_AVAILABLE:
            raise ImportError("asyncpg is required for PostgreSQL storage")
        
        self.dsn = dsn
        self.table_name = table_name
        self.pool: Optional[asyncpg.Pool] = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get PostgreSQL connection pool"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(self.dsn)
            await self._create_table()
        return self.pool
    
    async def _create_table(self) -> None:
        """Create tokens table if it doesn't exist"""
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    username VARCHAR(255) PRIMARY KEY,
                    token_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP
                )
            """)
    
    async def save_token(self, username: str, token_data: TokenData) -> None:
        """Save token to PostgreSQL"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(f"""
                    INSERT INTO {self.table_name} (username, token_data, expires_at)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (username) 
                    DO UPDATE SET token_data = $2, expires_at = $3, created_at = NOW()
                """, username, json.dumps(token_data.to_dict()), token_data.expires_at)
            
            LOGGER.info(f"Token saved to PostgreSQL for user: {username}")
        except Exception as e:
            LOGGER.error(f"Failed to save token to PostgreSQL: {e}")
            raise
    
    async def load_token(self, username: str) -> Optional[TokenData]:
        """Load token from PostgreSQL"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(f"""
                    SELECT token_data FROM {self.table_name} 
                    WHERE username = $1 AND (expires_at IS NULL OR expires_at > NOW())
                """, username)
                
                if row:
                    token_dict = json.loads(row['token_data'])
                    return TokenData.from_dict(token_dict)
                return None
        except Exception as e:
            LOGGER.error(f"Failed to load token from PostgreSQL: {e}")
            return None
    
    async def delete_token(self, username: str) -> None:
        """Delete token from PostgreSQL"""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(f"DELETE FROM {self.table_name} WHERE username = $1", username)
        except Exception as e:
            LOGGER.error(f"Failed to delete token from PostgreSQL: {e}")
    
    async def cleanup(self) -> None:
        """Close PostgreSQL connection pool"""
        if self.pool:
            await self.pool.close()


class TokenStorageFactory:
    """Factory for creating token storage backends"""
    
    @staticmethod
    def create_storage(backend: str, config: Optional[Dict[str, Any]] = None) -> TokenStorage:
        """Create token storage backend"""
        config = config or {}
        
        if backend == "redis":
            return RedisTokenStorage(
                config.get("redis_url", "redis://localhost:6379"),
                config.get("key_prefix", "dnse_token:")
            )
        elif backend == "postgres":
            return PostgresTokenStorage(
                config.get("dsn", "postgresql://user:pass@localhost/dbname"),
                config.get("table_name", "dnse_tokens")
            )
        else:
            raise ValueError(f"Unsupported storage backend: {backend}")


class DNSEAuthentication:
    """Enhanced DNSE Authentication with async support and multiple storage backends"""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.storage = TokenStorageFactory.create_storage(
            self.config.storage_backend, 
            self.config.storage_config
        )
        self.current_token_data: Optional[TokenData] = None

    
    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user and get access token"""
        try:
            # Hash password for security (if needed by API)
            data = {
                "username": username,
                "password": password  # Consider hashing if required
            }
            
            response_data = await self.make_request(
                "POST",
                "/dnse-auth-service/login",
                json_data=data
            )
            
            token = response_data.get("token")
            if not token:
                raise AuthenticationError("No token received from authentication")
            
            # Create token data
            created_at = datetime.now()
            expires_at = created_at + timedelta(hours=self.config.token_expiry_hours)
            
            self.current_token_data = TokenData(
                token=token,
                created_at=created_at,
                expires_at=expires_at,
                username=username
            )
            
            LOGGER.info(f"Authentication successful for user: {username}")
            return True
            
        except AuthenticationError as e:
            LOGGER.error(f"Authentication failed: {e.message}")
            return False
    
    async def send_email_otp(self) -> bool:
        """Send OTP via email"""
        if not self.current_token_data or not self.current_token_data.token:
            LOGGER.error("No valid token available for OTP request")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.current_token_data.token}"}
            
            await self.make_request(
                "GET",
                "/dnse-auth-service/api/email-otp",
                headers=headers
            )
            
            LOGGER.info("Email OTP sent successfully!")
            return True
            
        except AuthenticationError as e:
            LOGGER.error(f"Failed to send email OTP: {e.message}")
            return False
    
    async def get_trading_token(self, otp: str, otp_type: OTPType = OTPType.EMAIL) -> bool:
        """Get trading token using OTP"""
        if not self.current_token_data or not self.current_token_data.token:
            LOGGER.error("No valid token available for trading token request")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.current_token_data.token}"}
            
            if otp_type == OTPType.SMART:
                headers["smart-otp"] = otp
            elif otp_type == OTPType.EMAIL:
                headers["otp"] = otp
            
            response_data = await self.make_request(
                "POST",
                "/dnse-order-service/trading-token",
                headers=headers
            )
            
            trading_token = response_data.get("tradingToken")
            if not trading_token:
                raise AuthenticationError("No trading token received")
            
            # Update current token data
            self.current_token_data.trading_token = trading_token
            
            # Save to storage
            if self.current_token_data.username:
                await self.storage.save_token(self.current_token_data.username, self.current_token_data)
            
            LOGGER.info("Trading token obtained and saved successfully!")
            return True
            
        except AuthenticationError as e:
            LOGGER.error(f"Failed to get trading token: {e.message}")
            return False
    
    async def load_token(self, username: str) -> bool:
        """Load token from storage"""
        try:
            token_data = await self.storage.load_token(username)
            
            if token_data and token_data.is_valid():
                self.current_token_data = token_data
                
                remaining = token_data.time_remaining()
                if remaining:
                    LOGGER.info(f"Token loaded successfully. Time remaining: {remaining}")
                else:
                    LOGGER.info("Token loaded successfully (no expiry)")
                
                return True
            else:
                if token_data:
                    LOGGER.warning("Token expired, please re-authenticate")
                    await self.storage.delete_token(username)
                else:
                    LOGGER.warning(f"No token found for user: {username}")
                return False
                
        except Exception as e:
            LOGGER.error(f"Failed to load token: {e}")
            return False
    
    async def refresh_token_if_needed(self, username: str, threshold_minutes: int = 30) -> bool:
        """Refresh token if it's close to expiry"""
        if not self.current_token_data:
            return False
        
        remaining = self.current_token_data.time_remaining()
        if remaining and remaining < timedelta(minutes=threshold_minutes):
            LOGGER.info(f"Token expires in {remaining}, refreshing...")
            # Here you might implement token refresh logic if the API supports it
            # For now, we'll just indicate that re-authentication is needed
            return False
        
        return True
    
    async def logout(self, username: str) -> None:
        """Logout and clean up tokens"""
        try:
            await self.storage.delete_token(username)
            self.current_token_data = None
            LOGGER.info(f"Logged out user: {username}")
        except Exception as e:
            LOGGER.error(f"Error during logout: {e}")
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        
        await self.storage.cleanup()
    
    @property
    def token(self) -> Optional[str]:
        """Get current access token"""
        return self.current_token_data.token if self.current_token_data else None
    
    @property
    def trading_token(self) -> Optional[str]:
        """Get current trading token"""
        return self.current_token_data.trading_token if self.current_token_data else None
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return (self.current_token_data is not None and 
                self.current_token_data.token is not None and 
                self.current_token_data.is_valid())
    
    @property
    def has_trading_token(self) -> bool:
        """Check if trading token is available"""
        return (self.is_authenticated and 
                self.current_token_data.trading_token is not None)


# Usage example
async def main():
    """Example usage of the refactored authentication system"""
    
    # Configuration for different storage backends
    
    # File storage (default)
    file_config = AuthConfig(storage_backend="file")
    
    # Redis storage
    redis_config = AuthConfig(
        storage_backend="redis",
        storage_config={"redis_url": "redis://localhost:6379"}
    )
    
    # PostgreSQL storage
    postgres_config = AuthConfig(
        storage_backend="postgres",
        storage_config={"dsn": "postgresql://user:pass@localhost/dbname"}
    )
    
    # Initialize authentication client
    auth = DNSEAuthentication(file_config)
    
    try:
        username = "your_username"
        password = "your_password"
        
        # Try to load existing token
        if await auth.load_token(username):
            LOGGER.info("Using existing token")
        else:
            # Authenticate and get new token
            if await auth.authenticate(username, password):
                # Send OTP
                if await auth.send_email_otp():
                    # Get OTP from user input
                    otp = input("Enter OTP: ")
                    await auth.get_trading_token(otp, OTPType.EMAIL)
        
        # Check if we have valid tokens
        if auth.has_trading_token:
            LOGGER.info("Ready for trading operations")
            print(f"Access Token: {auth.token}")
            print(f"Trading Token: {auth.trading_token}")
        else:
            LOGGER.error("Failed to obtain trading token")
    
    finally:
        await auth.cleanup()


if __name__ == "__main__":
    asyncio.run(main())