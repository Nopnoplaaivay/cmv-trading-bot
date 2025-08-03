import os
from typing import Optional


class TelegramConfig:
    def __init__(self):
        self.bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
        self.admin_chat_id: Optional[str] = os.getenv("TELEGRAM_ADMIN_CHAT_ID")

        self.enable_trade_alerts: bool = (os.getenv("TELEGRAM_TRADE_ALERTS", "true").lower() == "true")
        self.enable_portfolio_updates: bool = (os.getenv("TELEGRAM_PORTFOLIO_UPDATES", "true").lower() == "true")
        self.enable_system_alerts: bool = (os.getenv("TELEGRAM_SYSTEM_ALERTS", "true").lower() == "true")
        self.enable_market_alerts: bool = (os.getenv("TELEGRAM_MARKET_ALERTS", "false").lower() == "true")

        self.max_retries: int = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))
        self.retry_delay: float = float(os.getenv("TELEGRAM_RETRY_DELAY", "1.0"))

        self.silent_hours_start: int = int(os.getenv("TELEGRAM_SILENT_START", "22"))
        self.silent_hours_end: int = int(os.getenv("TELEGRAM_SILENT_END", "7")) 

    def is_enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def is_silent_hour(self) -> bool:
        from datetime import datetime

        current_hour = datetime.now().hour

        if self.silent_hours_start <= self.silent_hours_end:
            return not (self.silent_hours_start <= current_hour < self.silent_hours_end)
        else:
            return not (
                current_hour >= self.silent_hours_start
                or current_hour < self.silent_hours_end
            )


telegram_config = TelegramConfig()
