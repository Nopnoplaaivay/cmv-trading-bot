import asyncio
import os
import time
from enum import Enum

from backend.common.configs.dnse import TradingAPIConfig
from backend.modules.dnse.trading_session import DNSESession
from backend.utils.logger import LOGGER


class OTPType(Enum):
    SMART = "smart"
    EMAIL = "email"


async def main():
    """Test DNSE client using Session pattern - no manual token passing needed"""
    config = TradingAPIConfig()

    async with DNSESession(config=config) as session:
        try:
            username = os.getenv("TEST_DNSE_ACCOUNT")
            password = os.getenv("TEST_DNSE_PASSWORD")

            # Authenticate - tokens are automatically managed
            if await session.authenticate(username, password):
                if not session.trading_token:  # Need OTP
                    if await session.send_otp():
                        otp = input("Enter OTP: ")
                        if await session.complete_auth(otp):
                            LOGGER.info("Trading token obtained successfully!")
                            LOGGER.info(f"Trading Token: {session.trading_token}")
                        else:
                            LOGGER.error("Failed to obtain trading token")
                            return
                else:
                    LOGGER.info("Using existing token")

                # Use clients with auto-injected tokens and auto-cleanup
                async with session.users_client() as users_client:
                    try:
                        users_info = await users_client.get_users_info()
                        LOGGER.info("Successfully got user info")
                    except Exception as e:
                        LOGGER.error(f"Failed to get user info: {e}")

                async with session.orders_client() as orders_client:
                    try:
                        # Example: Get account info or place orders
                        # account_info = await orders_client.get_account_info()
                        LOGGER.info("Orders client ready for use")
                    except Exception as e:
                        LOGGER.error(f"Failed to use orders client: {e}")

            else:
                LOGGER.error("Failed to authenticate")

        except Exception as e:
            LOGGER.error(f"Authentication error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
