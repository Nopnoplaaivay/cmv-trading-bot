import asyncio
import os

from backend.modules.dnse.session import DNSESession
from backend.utils.logger import LOGGER




async def main_with_session():
    async with DNSESession() as session:
        username = os.getenv("TEST_DNSE_ACCOUNT")
        password = os.getenv("TEST_DNSE_PASSWORD")

        if await session.authenticate(username, password):

            auth_status = session.get_auth_status()
            print(f"Auth status: {auth_status}")

            if not session.trading_token:
                await session.send_otp()
                otp = input("Enter OTP: ")
                await session.complete_auth(otp)

        if session.is_jwt_authenticated():
            async with session.users_client() as users_client:
                users_info = await users_client.get_users_info()
        else:
            print("❌ No JWT token - cannot access user info")

        if session.is_fully_authenticated():
            async with session.orders_client() as orders_client:
                print("Orders client ready for use")
        else:
            print("❌ No trading token - cannot place orders")


if __name__ == "__main__":
    asyncio.run(main_with_session())
