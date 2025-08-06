from typing import Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager

from backend.modules.notifications.telegram import TelegramNotifier, MessageType
from backend.common.configs.telegram import telegram_config
from backend.utils.logger import LOGGER


class NotificationService:
    def __init__(self):
        self.telegram: Optional[TelegramNotifier] = None
        self._initialized = False

    async def initialize(self) -> bool:
        if not telegram_config.is_enabled():
            LOGGER.warning("Telegram notifications not configured - missing bot token or chat ID")
            return False

        try:
            self.telegram = TelegramNotifier(
                bot_token=telegram_config.bot_token,
                chat_id=telegram_config.chat_id,
                max_retries=telegram_config.max_retries,
                retry_delay=telegram_config.retry_delay,
            )

            if await self.telegram.test_connection():
                self._initialized = True
                LOGGER.info("Notification service initialized successfully")
                return True
            else:
                LOGGER.error("Failed to connect to Telegram")
                return False

        except Exception as e:
            LOGGER.error(f"Failed to initialize notification service: {e}")
            return False

    def is_ready(self) -> bool:
        return self._initialized and self.telegram is not None


    async def notify_daily_portfolio(
        self, portfolio_data: Dict[str, Any]
    ) -> None:
        """Notify about daily portfolio weights."""
        if not self.is_ready():
            LOGGER.warning("Notification service not initialized")
            return

        try:
            await self.telegram.send_model_portfolio_update(portfolio_data=portfolio_data)
            LOGGER.info(f"Daily portfolio notification sent successfully")
        except Exception as e:
            LOGGER.error(f"Failed to send daily portfolio notification: {e}")


    # async def notify_trade_execution(
    #     self,
    #     symbol: str,
    #     side: str,
    #     quantity: int,
    #     price: float,
    #     account: str,
    #     order_id: Optional[str] = None,
    #     status: str = "EXECUTED",
    # ):
    #     if not self.is_ready() or not telegram_config.enable_trade_alerts:
    #         return

    #     try:
    #         await self.telegram.send_trade_alert(
    #             symbol=symbol,
    #             side=side,
    #             quantity=quantity,
    #             price=price,
    #             account=account,
    #             order_id=order_id,
    #             status=status,
    #         )
    #     except Exception as e:
    #         LOGGER.error(f"Failed to send trade notification: {e}")

    # async def notify_portfolio_update(
    #     self,
    #     total_value: float,
    #     cash: float,
    #     stocks_value: float,
    #     daily_pnl: float,
    #     daily_pnl_percent: float,
    # ):
    #     """Notify about portfolio updates."""
    #     if not self.is_ready() or not telegram_config.enable_portfolio_updates:
    #         return

    #     try:
    #         await self.telegram.send_portfolio_update(
    #             total_value=total_value,
    #             cash=cash,
    #             stocks_value=stocks_value,
    #             daily_pnl=daily_pnl,
    #             daily_pnl_percent=daily_pnl_percent,
    #         )
    #     except Exception as e:
    #         LOGGER.error(f"Failed to send portfolio notification: {e}")

    async def notify_system_event(
        self, title: str, description: str, alert_type: MessageType = MessageType.INFO
    ):
        """Notify about system events."""
        if not self.is_ready() or not telegram_config.enable_system_alerts:
            return

        try:
            # Use admin chat for critical system alerts if available
            chat_id = (
                telegram_config.admin_chat_id
                if alert_type == MessageType.ERROR
                else None
            )

            if chat_id and chat_id != telegram_config.chat_id:
                # Send to admin chat for critical alerts
                admin_notifier = TelegramNotifier(
                    bot_token=telegram_config.bot_token, chat_id=chat_id
                )
                await admin_notifier.send_system_alert(title, description, alert_type)

            # Also send to main chat
            await self.telegram.send_system_alert(title, description, alert_type)

        except Exception as e:
            LOGGER.error(f"Failed to send system notification: {e}")

    # async def notify_authentication(
    #     self, account: str, event: str, success: bool = True
    # ):
    #     """Notify about authentication events."""
    #     if not self.is_ready() or not telegram_config.enable_system_alerts:
    #         return

    #     try:
    #         await self.telegram.send_auth_alert(account, event, success)
    #     except Exception as e:
    #         LOGGER.error(f"Failed to send auth notification: {e}")

    # async def notify_market_alert(
    #     self,
    #     symbol: str,
    #     current_price: float,
    #     change: float,
    #     change_percent: float,
    #     volume: int,
    # ):
    #     """Notify about market data alerts."""
    #     if not self.is_ready() or not telegram_config.enable_market_alerts:
    #         return

    #     try:
    #         await self.telegram.send_market_data_alert(
    #             symbol=symbol,
    #             current_price=current_price,
    #             change=change,
    #             change_percent=change_percent,
    #             volume=volume,
    #         )
    #     except Exception as e:
    #         LOGGER.error(f"Failed to send market notification: {e}")

    # async def send_custom_message(
    #     self,
    #     message: str,
    #     message_type: MessageType = MessageType.INFO,
    #     disable_notification: bool = None,
    # ):
    #     """Send a custom message."""
    #     if not self.is_ready():
    #         return

    #     try:
    #         # Auto-detect if should be silent based on time
    #         if disable_notification is None:
    #             disable_notification = telegram_config.is_silent_hour()

    #         await self.telegram.send_message(
    #             text=message,
    #             message_type=message_type,
    #             disable_notification=disable_notification,
    #         )
    #     except Exception as e:
    #         LOGGER.error(f"Failed to send custom notification: {e}")


# Global notification service instance
notification_service = NotificationService()


@asynccontextmanager
async def notification_context():
    """
    Context manager for notification service.
    Automatically initializes and cleans up notification service.
    """
    try:
        await notification_service.initialize()
        yield notification_service
    finally:
        # Cleanup if needed
        pass


# Convenience functions for direct use
async def notify_trade(
    symbol: str, side: str, quantity: int, price: float, account: str, **kwargs
):
    """Quick function to notify about trades."""
    await notification_service.notify_trade_execution(
        symbol, side, quantity, price, account, **kwargs
    )


async def notify_error(title: str, description: str):
    """Quick function to notify about errors."""
    await notification_service.notify_system_event(
        title, description, MessageType.ERROR
    )


async def notify_success(title: str, description: str):
    """Quick function to notify about success events."""
    await notification_service.notify_system_event(
        title, description, MessageType.SUCCESS
    )


async def notify_warning(title: str, description: str):
    """Quick function to notify about warnings."""
    await notification_service.notify_system_event(
        title, description, MessageType.WARNING
    )
