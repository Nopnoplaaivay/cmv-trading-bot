import asyncio
import os
import time
from enum import Enum


from backend.common.configs.dnse import AuthConfig
from backend.modules.dnse.trading_api import AuthClient
from backend.utils.logger import LOGGER


class OTPType(Enum):
    SMART = "smart"
    EMAIL = "email"

async def main():

    auth_config = AuthConfig()
    auth_client = AuthClient(config=auth_config)

    try:
        username = os.getenv("TEST_DNSE_ACCOUNT")
        password = os.getenv("TEST_DNSE_PASSWORD")


        if await auth_client.load_token(username):
            LOGGER.info("Using existing token")
        else:
            if await auth_client.login(username, password):
                if await auth_client.send_email_otp():
                    otp = input("Enter OTP: ")
                    if await auth_client.get_trading_token(otp=otp, otp_type=OTPType.EMAIL.value):
                        LOGGER.info("Trading token obtained successfully!")
                        LOGGER.info(f"Trading Token: {auth_client.trading_token}")
                    else:
                        LOGGER.error("Failed to obtain trading token")
    
    finally:
        await auth_client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())