import asyncio
import os
from enum import Enum

from backend.modules.dnse.trading_session import TradingSession
from backend.utils.logger import LOGGER


class OrderSide(Enum):
    BUY = "NB"
    SELL = "NS"


class OrderType(Enum):
    MARKET = "MP"
    LIMIT = "LO"


async def main_with_session():
    async with TradingSession() as session:
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
                accounts_info = await users_client.get_user_accounts()
                # buying_power = await users_client.get_buying_power(
                #     account_no=accounts_info["default"]["id"],
                #     symbol="OCB",
                #     price=12000,
                #     load_package_id="1036",
                # )

        else:
            print("❌ No JWT token - cannot access user info")

        if session.is_fully_authenticated():
            async with session.orders_client() as orders_client:
                # Place an order
                order = await orders_client.place_order(
                    account_no=accounts_info["default"]["id"],
                    side=OrderSide.BUY.value,
                    order_type=OrderType.LIMIT.value,
                    symbol="MBS",
                    price=35200,
                    quantity=1,
                    loan_package_id="1036"
                )
                if order:
                    print(f"✅ Order placed successfully!")
                else:
                    print("❌ Failed to place order")

                # Get order book and order detail
                order_books = await orders_client.get_order_book(
                    account_no=accounts_info["default"]["id"]
                )
                if order_books:
                    print(f"✅ Order books retrieved successfully!")
                else:
                    print("❌ Failed to retrieve order books")

                order_detail = await orders_client.get_order_detail(
                    order_id=order["id"],
                    account_no=accounts_info["default"]["id"]
                )
                if order_detail:
                    print(f"✅ Order detail retrieved successfully!")
                else:
                    print("❌ Failed to retrieve order detail")

                # Cancel an order
                cancel_order = await orders_client.cancel_order(
                    order_id=order["id"],
                    account_no=accounts_info["default"]["id"]
                )
                if cancel_order:
                    print(f"✅ Order cancelled successfully!")
                else:
                    print("❌ Failed to cancel order")

            print("✅ Trading session completed successfully!")
        else:
            print("❌ No trading token - cannot place orders")


if __name__ == "__main__":
    asyncio.run(main_with_session())
