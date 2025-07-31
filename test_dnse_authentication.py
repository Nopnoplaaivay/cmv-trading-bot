import asyncio
import os
import time
from enum import Enum


from backend.common.configs.dnse import AuthConfig
from backend.modules.dnse.trading_api import TokensClient
from backend.utils.logger import LOGGER


class OTPType(Enum):
    SMART = "smart"
    EMAIL = "email"

async def main():

    auth_config = AuthConfig()
    auth = TokensClient(config=auth_config)

    try:
        username = os.getenv("TEST_DNSE_ACCOUNT")
        password = os.getenv("TEST_DNSE_PASSWORD")

        if await auth.load_token(username):
            LOGGER.info("Using existing token")
        else:
            if await auth.get_jwt_token(username, password):
                if await auth.send_email_otp():
                    otp = input("Enter OTP: ")
                    if await auth.get_new_trading_token(otp=otp, otp_type=OTPType.EMAIL.value):
                        LOGGER.info("Trading token obtained successfully!")
                        LOGGER.info(f"Trading Token: {auth.trading_token}")
                    else:
                        LOGGER.error("Failed to obtain trading token")

        # if auth.has_trading_token:
        #     LOGGER.info("Ready for trading operations")
        #     print(f"Access Token: {auth.token}")
        #     print(f"Trading Token: {auth.trading_token}")
        # else:
        #     LOGGER.error("Failed to obtain trading token")
    
    finally:
        await auth.cleanup()

if __name__ == "__main__":
    asyncio.run(main())