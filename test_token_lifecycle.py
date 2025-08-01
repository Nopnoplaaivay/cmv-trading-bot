"""
Test script for validating the enhanced token lifecycle management
with separate JWT and trading token timestamps.
"""
import asyncio
from backend.modules.dnse.trading_session import DNSESession
from backend.modules.dnse.entities.trading_tokens import TradingTokens
from backend.db.sessions.backend import SQLServerBackendSession


async def test_separate_token_timestamps():
    """Test the separate timestamp tracking for JWT and trading tokens."""
    print("🔧 Testing separate token timestamp validation...")
    
    async with SQLServerBackendSession() as db_session:
        # Create a test token entity with separate timestamps
        test_token = TradingTokens(
            account="test_account",
            jwtToken="test_jwt_token_12345",
            tradingToken="test_trading_token_67890",
            broker="DNSE"
        )
        
        # Simulate different creation times
        test_token.jwtCreatedAt = "2024-01-01 09:00:00"  # JWT created at login
        test_token.tradingCreatedAt = "2024-01-01 09:05:00"  # Trading token created 5 minutes later
        
        print(f"JWT Created At: {test_token.jwtCreatedAt}")
        print(f"Trading Created At: {test_token.tradingCreatedAt}")
        
        # Test JWT validation
        jwt_valid = test_token.is_jwt_valid()
        print(f"JWT Valid: {jwt_valid}")
        
        # Test trading token validation
        trading_valid = test_token.is_trading_token_valid()
        print(f"Trading Token Valid: {trading_valid}")
        
        # Test separate time remaining calculations
        jwt_remaining = test_token.jwt_time_remaining()
        trading_remaining = test_token.trading_time_remaining()
        
        print(f"JWT Time Remaining: {jwt_remaining} seconds")
        print(f"Trading Token Time Remaining: {trading_remaining} seconds")
        
        # Test the combined validation method
        combined_valid = test_token.is_valid()
        print(f"Combined Token Valid: {combined_valid}")


async def test_auth_client_flow():
    """Test the authentication client with separate timestamp tracking."""
    print("\n🔧 Testing authentication client flow...")
    
    try:
        async with DNSESession() as session:
            # Test login (should set jwtCreatedAt)
            print("Attempting login...")
            login_result = await session.auth_client.login(
                username="test_user",
                password="test_password"
            )
            print(f"Login Result: {login_result}")
            
            # Test get trading token (should set tradingCreatedAt)
            print("Attempting to get trading token...")
            token_result = await session.auth_client.get_trading_token(
                otp="123456"
            )
            print(f"Trading Token Result: {token_result}")
            
    except Exception as e:
        print(f"⚠️ Authentication test failed (expected for test credentials): {e}")


async def test_token_lifecycle_edge_cases():
    """Test edge cases in token lifecycle management."""
    print("\n🔧 Testing token lifecycle edge cases...")
    
    # Test token with only JWT (no trading token yet)
    jwt_only_token = TradingTokens(
        account="jwt_only_account",
        jwtToken="jwt_token_only",
        tradingToken=None,
        broker="DNSE"
    )
    jwt_only_token.jwtCreatedAt = "2024-01-01 09:00:00"
    jwt_only_token.tradingCreatedAt = None
    
    print(f"JWT-Only Token Valid: {jwt_only_token.is_valid()}")
    print(f"JWT Valid: {jwt_only_token.is_jwt_valid()}")
    print(f"Trading Token Valid: {jwt_only_token.is_trading_token_valid()}")
    
    # Test expired JWT but valid trading token
    mixed_token = TradingTokens(
        account="mixed_account",
        jwtToken="expired_jwt",
        tradingToken="valid_trading_token",
        broker="DNSE"
    )
    # JWT expired (more than 24 hours ago)
    mixed_token.jwtCreatedAt = "2023-01-01 09:00:00"
    # Trading token valid (less than 8 hours ago)
    mixed_token.tradingCreatedAt = "2024-01-01 09:00:00"
    
    print(f"Mixed Token Valid: {mixed_token.is_valid()}")
    print(f"Expired JWT Valid: {mixed_token.is_jwt_valid()}")
    print(f"Valid Trading Token: {mixed_token.is_trading_token_valid()}")


if __name__ == "__main__":
    asyncio.run(test_separate_token_timestamps())
    asyncio.run(test_auth_client_flow())
    asyncio.run(test_token_lifecycle_edge_cases())
    print("\n✅ Token lifecycle testing completed!")
