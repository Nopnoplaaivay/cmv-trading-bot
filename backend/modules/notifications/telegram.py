import asyncio
import aiohttp
import ssl
import os
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime

from backend.common.consts import SQLServerConsts
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils


LOGGER_PREFIX = "[Telegram]"


class MessageType(Enum):
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    TRADE_BUY = "🟢"
    TRADE_SELL = "🔴"
    MONEY = "💰"
    CHART = "📊"
    ROBOT = "🤖"


class TelegramNotifier:
    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 60,  # Increase default timeout for Docker
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

        self._last_send_time = 0
        self._min_interval = 0.05

        # Create SSL context for better connection handling
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED

        # For Docker environments, allow for more flexible SSL
        import os

        if os.getenv("DOCKER_ENV", "false").lower() == "true":
            LOGGER.info(f"{LOGGER_PREFIX} Running in Docker environment - adjusting SSL settings")
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

    async def _rate_limit(self):
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_send_time

        if time_since_last < self._min_interval:
            await asyncio.sleep(self._min_interval - time_since_last)

        self._last_send_time = asyncio.get_event_loop().time()

    async def send_message(
        self,
        text: str,
        message_type: MessageType = MessageType.INFO,
        parse_mode: str = "HTML",
        disable_notification: bool = False,
    ) -> bool:
        await self._rate_limit()

        timestamp = TimeUtils.get_current_vn_time().strftime("%H:%M:%S")
        formatted_text = f"{message_type.value} <b>[{timestamp}]</b> {text}"

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": formatted_text,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
        }

        for attempt in range(self.max_retries):
            try:
                # Create connector with specific SSL and DNS settings optimized for Docker
                connector = aiohttp.TCPConnector(
                    ssl=self.ssl_context,
                    limit=10,
                    limit_per_host=5,
                    enable_cleanup_closed=True,
                    resolver=aiohttp.resolver.DefaultResolver(),
                    family=0,  # Allow both IPv4 and IPv6
                    local_addr=None,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )

                # Increase timeouts for Docker environment
                connect_timeout = (
                    20 if os.getenv("DOCKER_ENV", "false").lower() == "true" else 10
                )
                sock_read_timeout = (
                    20 if os.getenv("DOCKER_ENV", "false").lower() == "true" else 10
                )

                timeout = aiohttp.ClientTimeout(
                    total=self.timeout,
                    connect=connect_timeout,
                    sock_read=sock_read_timeout,
                )

                async with aiohttp.ClientSession(
                    connector=connector, timeout=timeout
                ) as session:
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            LOGGER.info(
                                f"{LOGGER_PREFIX} Telegram message sent successfully (attempt {attempt + 1})"
                            )
                            return True
                        else:
                            error_text = await response.text()
                            LOGGER.warning(
                                f"{LOGGER_PREFIX} Telegram API error: {response.status} - {error_text}"
                            )

            except asyncio.TimeoutError:
                LOGGER.error(
                    f"{LOGGER_PREFIX} Telegram API timeout (attempt {attempt + 1}) - Consider checking network connectivity in Docker"
                )
            except aiohttp.ClientConnectorError as e:
                LOGGER.error(f"{LOGGER_PREFIX} Telegram connection error (attempt {attempt + 1}): {e}")
                # Log additional info for Docker debugging
                if os.getenv("DOCKER_ENV", "false").lower() == "true":
                    LOGGER.error(
                        f"{LOGGER_PREFIX} Docker environment detected. This might be a DNS/network issue. Check:"
                    )
                    LOGGER.error(f"{LOGGER_PREFIX} 1. Container has internet access")
                    LOGGER.error(f"{LOGGER_PREFIX} 2. DNS resolution is working")
                    LOGGER.error(f"{LOGGER_PREFIX} 3. Firewall rules allow outbound HTTPS")
            except ssl.SSLError as e:
                LOGGER.error(f"{LOGGER_PREFIX} Telegram SSL error (attempt {attempt + 1}): {e}")
            except Exception as e:
                LOGGER.error(
                    f"{LOGGER_PREFIX} Failed to send Telegram message (attempt {attempt + 1}): {e}"
                )

            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        LOGGER.error(
            f"{LOGGER_PREFIX} Failed to send Telegram message after {self.max_retries} attempts"
        )
        return False

    async def send_model_portfolio_update(self, portfolio_data: Dict):
        date = portfolio_data["date"]
        long_only = portfolio_data["LongOnly"]
        market_neutral = portfolio_data["MarketNeutral"]

        date_display = datetime.strptime(date, SQLServerConsts.DATE_FORMAT).strftime(
            "%d/%m/%Y"
        )

        message = f"""
<b>📊 BÁO CÁO DANH MỤC ĐẦU TƯ NGÀY GIAO DỊCH TIẾP THEO</b>
<b>📅 Ngày giao dịch: {date_display}</b>

<b>📈 DANH MỤC LONG-ONLY ({len(long_only)} mã)</b>
"""

        # Add long-only positions
        if long_only:
            total_long_weight = sum(pos["weight"] for pos in long_only)
            for i, pos in enumerate(long_only[:15], 1):  # Top 15 positions
                message += f"{i:2d}. <b>{pos['symbol']}</b>: {pos['weight']:.2f}%\n"

            if len(long_only) > 15:
                remaining = len(long_only) - 15
                message += f"    ... và {remaining} mã khác\n"

            message += f"\n💰 <b>Tổng tỷ trọng:</b> {total_long_weight:.2f}%\n"
        else:
            message += "Không có vị thế nào\n"

        message += f"\n<b>⚖️ DANH MỤC MARKET NEUTRAL ({len(market_neutral)} mã)</b>\n"

        # Add market neutral positions
        if market_neutral:
            long_positions = [pos for pos in market_neutral if pos["weight"] > 0]
            short_positions = [pos for pos in market_neutral if pos["weight"] < 0]

            # Long positions
            if long_positions:
                message += f"\n🟢 <b>VỊ THẾ LONG ({len(long_positions)} mã):</b>\n"
                for i, pos in enumerate(long_positions[:20], 1):  # Top 10
                    message += f"{i:2d}. <b>{pos['symbol']}</b>: {pos['weight']:.2f}%\n"

            # Short positions
            if short_positions:
                message += f"\n🔴 <b>VỊ THẾ SHORT ({len(short_positions)} mã):</b>\n"
                for i, pos in enumerate(short_positions[:20], 1):  # Top 10
                    message += f"{i:2d}. <b>{pos['symbol']}</b>: {pos['weight']:.2f}%\n"

            # Summary
            # total_long = sum(pos["weight"] for pos in long_positions)
            # total_short = sum(pos["weight"] for pos in short_positions)
            # message += f"\n📊 <b>Tổng kết:</b> Long {total_long:+.2f}% | Short {total_short:+.2f}% | Net {(total_long+total_short):+.2f}%"
        else:
            message += "Không có vị thế nào\n"

        message += f"\n\n🤖 <i>Được tạo tự động lúc {TimeUtils.get_current_vn_time().strftime('%H:%M:%S %d/%m/%Y')}</i>"

        await self.send_message(message, MessageType.CHART, disable_notification=False)

    async def send_system_alert(
        self,
        title: str,
        description: str,
        alert_type: MessageType = MessageType.WARNING,
    ):
        message = f"""
            <b>{alert_type.value} {title}</b>

            {description}

            ⏰ <i>Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>
        """

        await self.send_message(message, alert_type)

    async def test_connection(self) -> bool:
        try:
            url = f"{self.base_url}/getMe"

            # Create connector with Docker-optimized settings
            connector = aiohttp.TCPConnector(
                ssl=self.ssl_context,
                limit=10,
                limit_per_host=5,
                enable_cleanup_closed=True,
                resolver=aiohttp.resolver.DefaultResolver(),
                family=0,  # Allow both IPv4 and IPv6
                local_addr=None,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )

            # Increase timeouts for Docker environment
            connect_timeout = (
                20 if os.getenv("DOCKER_ENV", "false").lower() == "true" else 10
            )
            sock_read_timeout = (
                20 if os.getenv("DOCKER_ENV", "false").lower() == "true" else 10
            )

            timeout = aiohttp.ClientTimeout(
                total=self.timeout, connect=connect_timeout, sock_read=sock_read_timeout
            )

            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        bot_info = data.get("result", {})
                        LOGGER.info(
                            f"{LOGGER_PREFIX} Telegram bot connected successfully: @{bot_info.get('username', 'unknown')}"
                        )
                        # await self.send_message(
                        #     f"🤖 Bot kết nối thành công!\n"
                        #     f"📛 Tên bot: {bot_info.get('first_name', 'Unknown')}\n"
                        #     f"🆔 Username: @{bot_info.get('username', 'unknown')}",
                        #     MessageType.SUCCESS,
                        # )
                        return True
                    else:
                        error_text = await response.text()
                        LOGGER.error(
                            f"{LOGGER_PREFIX} Telegram bot test failed: {response.status} - {error_text}"
                        )
                        return False
        except asyncio.TimeoutError:
            LOGGER.error(f"{LOGGER_PREFIX} Telegram connection test error: Connection timeout")
            return False
        except aiohttp.ClientConnectorError as e:
            LOGGER.error(
                f"{LOGGER_PREFIX} Telegram connection test error: Cannot connect to host api.telegram.org:443 ssl:default [{e}]"
            )
            return False
        except ssl.SSLError as e:
            LOGGER.error(f"{LOGGER_PREFIX} Telegram connection test error: SSL error [{e}]")
            return False
        except Exception as e:
            LOGGER.error(f"{LOGGER_PREFIX} Telegram connection test error: {e}")
            return False

    # async def send_trade_alert(
    #     self,
    #     symbol: str,
    #     side: str,
    #     quantity: int,
    #     price: float,
    #     account: str,
    #     order_id: Optional[str] = None,
    #     status: str = "PLACED",
    # ):
    #     side_emoji = (
    #         MessageType.TRADE_BUY
    #         if side.upper() in ["BUY", "NB"]
    #         else MessageType.TRADE_SELL
    #     )
    #     side_text = "MUA" if side.upper() in ["BUY", "NB"] else "BÁN"

    #     message = f"""
    #         <b>🎯 LỆNH GIAO DỊCH - {status}</b>

    #         📈 <b>Mã CK:</b> {symbol}
    #         {side_emoji.value} <b>Loại:</b> {side_text}
    #         📊 <b>Số lượng:</b> {quantity:,} cổ phiếu
    #         💰 <b>Giá:</b> {price:,} VND
    #         👤 <b>Tài khoản:</b> {account}
    #     """

    #     if order_id:
    #         message += f"🔖 <b>Mã lệnh:</b> {order_id}"

    #     await self.send_message(message, MessageType.ROBOT)

    # async def send_portfolio_update(
    #     self,
    #     total_value: float,
    #     cash: float,
    #     stocks_value: float,
    #     daily_pnl: float,
    #     daily_pnl_percent: float,
    # ):
    #     pnl_emoji = MessageType.SUCCESS if daily_pnl >= 0 else MessageType.ERROR
    #     pnl_sign = "+" if daily_pnl >= 0 else ""

    #     message = f"""
    #         <b>📊 CẬP NHẬT DANH MỤC ĐẦU TƯ</b>

    #         💎 <b>Tổng tài sản:</b> {total_value:,.0f} VND
    #         💵 <b>Tiền mặt:</b> {cash:,.0f} VND
    #         📈 <b>Giá trị CP:</b> {stocks_value:,.0f} VND

    #         {pnl_emoji.value} <b>P&L hôm nay:</b> {pnl_sign}{daily_pnl:,.0f} VND ({pnl_sign}{daily_pnl_percent:.2f}%)
    #     """

    #     await self.send_message(message, MessageType.CHART)

    # async def send_market_data_alert(
    #     self,
    #     symbol: str,
    #     current_price: float,
    #     change: float,
    #     change_percent: float,
    #     volume: int,
    # ):
    #     change_emoji = MessageType.SUCCESS if change >= 0 else MessageType.ERROR
    #     change_sign = "+" if change >= 0 else ""

    #     message = f"""
    #         <b>📊 DỮ LIỆU THỊ TRƯỜNG - {symbol}</b>

    #         💰 <b>Giá hiện tại:</b> {current_price:,.0f} VND
    #         {change_emoji.value} <b>Thay đổi:</b> {change_sign}{change:,.0f} VND ({change_sign}{change_percent:.2f}%)
    #         📈 <b>Khối lượng:</b> {volume:,} CP
    #     """

    #     await self.send_message(message, MessageType.CHART)

    # async def send_auth_alert(self, account: str, event: str, success: bool = True):
    #     status_emoji = MessageType.SUCCESS if success else MessageType.ERROR
    #     status_text = "THÀNH CÔNG" if success else "THẤT BẠI"

    #     message = f"""
    #         <b>🔐 XANH THỰC {event.upper()} - {status_text}</b>

    #         👤 <b>Tài khoản:</b> {account}
    #         🕒 <b>Thời gian:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    #     """

    #     await self.send_message(message, status_emoji)


def create_telegram_notifier(
    bot_token: str, chat_id: str, **kwargs
) -> TelegramNotifier:
    """
    Create a TelegramNotifier instance with enhanced connection settings.

    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat ID
        **kwargs: Additional parameters (timeout, max_retries, retry_delay)
    """
    return TelegramNotifier(bot_token, chat_id, **kwargs)
