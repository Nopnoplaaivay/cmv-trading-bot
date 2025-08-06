import asyncio
import schedule
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
import pandas as pd

from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.auth.types import JwtPayload
from backend.modules.dnse.trading_session import TradingSession
from backend.modules.auth.entities import Users
from backend.modules.auth.repositories import UsersRepo
from backend.modules.portfolio.entities import (
    OptimizedWeights,
)
from backend.modules.portfolio.repositories import (
    AccountsRepo,
    OptimizedWeightsRepo,
)
from backend.modules.notifications.service import notification_service, notify_error
from backend.modules.notifications.telegram import MessageType
from backend.utils.time_utils import TimeUtils
from backend.utils.logger import LOGGER


LIMIT_WEIGHT_PCT = int(os.getenv("LIMIT_WEIGHT_PCT", 10))


# Value Objects
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "VND"

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * Decimal(str(factor)), self.currency)


@dataclass(frozen=True)
class Weight:
    percentage: Decimal

    def __post_init__(self):
        if not 0 <= self.percentage <= 100:
            raise ValueError("Weight must be between 0 and 100")


@dataclass(frozen=True)
class Position:
    symbol: str
    quantity: int
    market_price: Money
    cost_price: Money
    weight: Weight
    unrealized_profit: Money = None

    @property
    def market_value(self) -> Money:
        return self.market_price * self.quantity


@dataclass(frozen=True)
class TradeRecommendation:
    symbol: str
    action: str  # "BUY" or "SELL"
    current_weight: Weight
    target_weight: Weight
    amount: Money
    priority: str  # "HIGH", "MEDIUM", "LOW"
    reason: str


# Strategy Pattern for Portfolio Strategies
class PortfolioStrategy(ABC):
    @abstractmethod
    def get_target_weights(self, portfolio_data: Dict) -> List[Dict]:
        pass


class LongOnlyStrategy(PortfolioStrategy):
    def get_target_weights(self, portfolio_data: Dict) -> List[Dict]:
        return portfolio_data.get("long_only", [])


class MarketNeutralStrategy(PortfolioStrategy):
    def get_target_weights(self, portfolio_data: Dict) -> List[Dict]:
        return portfolio_data.get("market_neutral", [])


# Factory for strategies
class StrategyFactory:
    @staticmethod
    def create_strategy(strategy_type: str) -> PortfolioStrategy:
        strategies = {
            "long_only": LongOnlyStrategy(),
            "market_neutral": MarketNeutralStrategy(),
        }
        if strategy_type not in strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return strategies[strategy_type]


# Trading Calendar Service
class TradingCalendarService:
    @staticmethod
    def is_trading_day(date: datetime) -> bool:
        return date.weekday() < 5

    @staticmethod
    def get_last_trading_date(current_date: datetime) -> datetime:
        check_date = current_date - timedelta(days=1)
        while not TradingCalendarService.is_trading_day(check_date):
            check_date -= timedelta(days=1)
        return check_date


# Portfolio Data Provider
class PortfolioDataProvider:
    def __init__(self, repo: OptimizedWeightsRepo = OptimizedWeightsRepo):
        self.repo = repo

    async def get_portfolio_weights(
        self, last_trading_date: str, current_date: str
    ) -> Optional[Dict]:
        try:
            with self.repo.session_scope() as session:
                conditions = {OptimizedWeights.date.name: last_trading_date}
                records = await self.repo.get_by_condition(conditions=conditions)

                if not records:
                    LOGGER.warning(
                        f"No portfolio data found for date: {last_trading_date}"
                    )
                    return None

                long_only_positions = []
                market_neutral_positions = []

                for record in records:
                    symbol = record[OptimizedWeights.symbol.name]
                    initial_weight_pct = (
                        record[OptimizedWeights.initialWeight.name] * 100 or 0
                    )
                    neutralized_weight_pct = (
                        record[OptimizedWeights.neutralizedWeight.name] * 100 or 0
                    )

                    if initial_weight_pct > 1:
                        long_only_positions.append(
                            {
                                "symbol": symbol,
                                "weight": min(initial_weight_pct, LIMIT_WEIGHT_PCT),
                            }
                        )

                    if neutralized_weight_pct > 1:
                        market_neutral_positions.append(
                            {
                                "symbol": symbol,
                                "weight": min(neutralized_weight_pct, LIMIT_WEIGHT_PCT),
                            }
                        )

                long_only_positions.sort(key=lambda x: x["weight"], reverse=True)
                market_neutral_positions.sort(key=lambda x: x["weight"], reverse=True)
                session.commit()

            return {
                "date": current_date,
                "long_only": long_only_positions,
                "market_neutral": market_neutral_positions,
            }

        except Exception as e:
            LOGGER.error(
                f"Error getting portfolio weights for {last_trading_date}: {e}"
            )
            await notify_error(
                "PORTFOLIO DATA ERROR",
                f"Không thể lấy dữ liệu danh mục cho ngày {last_trading_date}: {str(e)}",
            )
            return None


# Account Data Provider
class AccountDataProvider:
    def __init__(self, accounts_repo: AccountsRepo = AccountsRepo):
        self.accounts_repo = accounts_repo

    async def get_trading_account(self, broker_account_id: str) -> Optional[Dict]:
        """Get trading account details by broker account ID"""
        existing_accounts = await self.accounts_repo.get_by_broker_account_id(
            broker_account_id=broker_account_id
        )

        if not existing_accounts:
            return None

        # Find trading account (type "0449")
        for account in existing_accounts:
            if account.get("accountType") == "0449":
                return account

        return None


# Portfolio Processor
class PortfolioProcessor:
    @staticmethod
    def process_deals_to_positions(
        deals_list: List[Dict], net_asset_value: float
    ) -> List[Position]:
        """Convert raw deals data into Position objects"""
        positions = []

        if not deals_list or net_asset_value <= 0:
            return positions

        for deal in deals_list:
            symbol = deal.get("symbol", "")
            if not symbol:
                continue

            accumulate_quantity = deal.get("accumulateQuantity", 0)
            market_price_value = deal.get("marketPrice", 0)
            cost_price_value = deal.get("averageCostPrice", 0)
            unrealized_profit_value = deal.get("unrealizedProfit", 0)

            if accumulate_quantity > 0 and market_price_value > 0:
                market_price = Money(Decimal(str(market_price_value)))
                cost_price = Money(Decimal(str(cost_price_value)))
                unrealized_profit = Money(Decimal(str(unrealized_profit_value)))

                market_value = market_price.amount * accumulate_quantity
                weight_pct = (market_value / Decimal(str(net_asset_value))) * 100
                weight = Weight(weight_pct)

                position = Position(
                    symbol=symbol,
                    quantity=accumulate_quantity,
                    market_price=market_price,
                    cost_price=cost_price,
                    weight=weight,
                    unrealized_profit=unrealized_profit,
                )
                positions.append(position)

        # Sort by weight descending
        positions.sort(key=lambda x: x.weight.percentage, reverse=True)
        return positions


# Recommendation Engine
class RecommendationEngine:
    def __init__(self, weight_tolerance: float = 2.0):
        self.weight_tolerance = weight_tolerance

    def generate_recommendations(
        self,
        current_positions: List[Position],
        target_weights: List[Dict],
        available_cash: Money,
        net_asset_value: Money,
    ) -> List[TradeRecommendation]:
        """Generate trade recommendations based on current vs target portfolio"""
        recommendations = []

        # Create lookup dictionaries
        current_dict = {pos.symbol: pos for pos in current_positions}
        target_dict = {weight["symbol"]: weight for weight in target_weights}

        all_symbols = set(current_dict.keys()) | set(target_dict.keys())

        for symbol in all_symbols:
            current_weight = current_dict.get(
                symbol,
                Position(
                    symbol=symbol,
                    quantity=0,
                    market_price=Money(Decimal("0")),
                    cost_price=Money(Decimal("0")),
                    weight=Weight(Decimal("0")),
                ),
            ).weight.percentage

            target_weight = Decimal(str(target_dict.get(symbol, {}).get("weight", 0)))
            weight_diff = target_weight - current_weight

            # Skip if within tolerance
            if abs(weight_diff) < self.weight_tolerance:
                continue

            priority = self._calculate_priority(abs(weight_diff))

            if weight_diff > self.weight_tolerance:  # Need to buy
                required_value = (target_weight / 100) * net_asset_value.amount
                current_value = current_dict.get(
                    symbol,
                    Position(
                        symbol=symbol,
                        quantity=0,
                        market_price=Money(Decimal("0")),
                        cost_price=Money(Decimal("0")),
                        weight=Weight(Decimal("0")),
                    ),
                ).market_value.amount

                cash_needed = Money(required_value - current_value)

                if cash_needed.amount > 0:
                    recommendation = TradeRecommendation(
                        symbol=symbol,
                        action="BUY",
                        current_weight=Weight(current_weight),
                        target_weight=Weight(target_weight),
                        amount=cash_needed,
                        priority=priority,
                        reason=f"Increase weight from {current_weight:.1f}% to {target_weight:.1f}%",
                    )
                    recommendations.append(recommendation)

            elif weight_diff < -self.weight_tolerance:  # Need to sell
                current_value = (
                    current_dict.get(symbol).market_value.amount
                    if symbol in current_dict
                    else Decimal("0")
                )
                target_value = (target_weight / 100) * net_asset_value.amount
                cash_to_raise = Money(current_value - target_value)

                recommendation = TradeRecommendation(
                    symbol=symbol,
                    action="SELL",
                    current_weight=Weight(current_weight),
                    target_weight=Weight(target_weight),
                    amount=cash_to_raise,
                    priority=priority,
                    reason=f"Reduce weight from {current_weight:.1f}% to {target_weight:.1f}%",
                )
                recommendations.append(recommendation)

        # Sort recommendations by priority and weight difference
        recommendations.sort(
            key=lambda x: (
                x.priority == "HIGH",
                abs(x.target_weight.percentage - x.current_weight.percentage),
            ),
            reverse=True,
        )
        return recommendations

    def _calculate_priority(self, weight_diff: Decimal) -> str:
        """Calculate priority based on weight difference"""
        if weight_diff > 3:
            return "HIGH"
        elif weight_diff > 1.5:
            return "MEDIUM"
        else:
            return "LOW"


# Report Generator
class PortfolioReportGenerator:
    @staticmethod
    def generate_text_report(
        account_id: str,
        strategy_type: str,
        positions: List[Position],
        recommendations: List[TradeRecommendation],
        account_balance: Dict,
        analysis_date: str,
        include_trade_plan: bool = True,
    ) -> str:
        """Generate a formatted text report"""
        report_lines = []
        report_lines.append("📊 **BÁO CÁO DANH MỤC ĐẦU TƯ**")
        report_lines.append(f"📅 Ngày: {analysis_date}")
        report_lines.append(f"💼 Tài khoản: {account_id}")
        report_lines.append(f"📈 Chiến lược: {strategy_type.replace('_', ' ').title()}")
        report_lines.append("")

        # Account balance summary
        report_lines.append("💰 **TÌNH HÌNH TÀI KHOẢN**")
        report_lines.append(
            f"• Tổng tài sản: {account_balance['net_asset_value']:,.0f} VND"
        )
        report_lines.append(
            f"• Tiền mặt khả dụng: {account_balance['available_cash']:,.0f} VND"
        )
        report_lines.append(f"• Tỷ lệ tiền mặt: {account_balance['cash_ratio']:.1f}%")
        report_lines.append("")

        # Current portfolio
        if positions:
            report_lines.append(f"📋 **DANH MỤC HIỆN TẠI** ({len(positions)} cổ phiếu)")
            for i, pos in enumerate(positions[:5], 1):  # Top 5 positions
                report_lines.append(
                    f"{i}. {pos.symbol}: {pos.weight.percentage:.1f}% "
                    f"({pos.quantity:,} cổ phiếu @ {pos.market_price.amount:,.0f} VND)"
                )
            if len(positions) > 5:
                report_lines.append(f"... và {len(positions) - 5} cổ phiếu khác")
            report_lines.append("")

        # Recommendations
        buy_recs = [r for r in recommendations if r.action == "BUY"]
        sell_recs = [r for r in recommendations if r.action == "SELL"]

        if recommendations:
            report_lines.append(
                f"🎯 **KHUYẾN NGHỊ GIAO DỊCH** ({len(recommendations)} giao dịch)"
            )

            if buy_recs:
                report_lines.append(f"📈 **MUA VÀO** ({len(buy_recs)} cổ phiếu):")
                for rec in buy_recs[:3]:
                    report_lines.append(
                        f"• {rec.symbol}: {rec.target_weight.percentage:.1f}% "
                        f"(cần {rec.amount.amount:,.0f} VND) - {rec.priority}"
                    )
                if len(buy_recs) > 3:
                    report_lines.append(f"... và {len(buy_recs) - 3} cổ phiếu khác")
                report_lines.append("")

            if sell_recs:
                report_lines.append(f"📉 **BÁN RA** ({len(sell_recs)} cổ phiếu):")
                for rec in sell_recs[:3]:
                    report_lines.append(
                        f"• {rec.symbol}: {rec.current_weight.percentage:.1f}% → {rec.target_weight.percentage:.1f}% "
                        f"(thu {rec.amount.amount:,.0f} VND) - {rec.priority}"
                    )
                if len(sell_recs) > 3:
                    report_lines.append(f"... và {len(sell_recs) - 3} cổ phiếu khác")
        else:
            report_lines.append("✅ **DANH MỤC ĐÃ CÂN BẰNG** - Không cần điều chỉnh")

        return "\n".join(report_lines)
        return "\n".join(report_lines)


# Main Portfolio Analysis Service
class PortfolioAnalysisService:
    def __init__(
        self,
        portfolio_data_provider: PortfolioDataProvider = None,
        account_data_provider: AccountDataProvider = None,
        recommendation_engine: RecommendationEngine = None,
        trading_calendar: TradingCalendarService = None,
    ):
        self.portfolio_data_provider = (
            portfolio_data_provider or PortfolioDataProvider()
        )
        self.account_data_provider = account_data_provider or AccountDataProvider()
        self.recommendation_engine = recommendation_engine or RecommendationEngine()
        self.trading_calendar = trading_calendar or TradingCalendarService()

    async def analyze_portfolio(
        self,
        user: JwtPayload,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
    ) -> Optional[Dict]:
        """Main method to analyze portfolio and generate recommendations"""
        try:
            LOGGER.info(
                f"Analyzing portfolio for user {user.userId} with account {broker_account_id}"
            )

            # Get account details
            trade_account = await self.account_data_provider.get_trading_account(
                broker_account_id
            )
            if not trade_account:
                LOGGER.warning(
                    f"No trading account found for broker_account_id: {broker_account_id}"
                )
                return None

            custody_code = trade_account.get("custodyCode")
            password = trade_account.get("password")

            # Authenticate and get current portfolio data
            async with TradingSession(account=custody_code) as session:
                if not await session.authenticate(password=password):
                    raise BaseExceptionResponse(
                        http_code=401,
                        status_code=401,
                        message=MessageConsts.UNAUTHORIZED,
                        errors="Authentication failed",
                    )

                async with session.users_client() as users_client:
                    balance_dict = await users_client.get_account_balance(
                        account_no=broker_account_id
                    )
                    deals_dict = await users_client.get_account_deals(
                        account_no=broker_account_id
                    )

                    if not balance_dict:
                        LOGGER.warning(
                            f"No balance data found for account {broker_account_id}"
                        )
                        return None

                    if not deals_dict:
                        LOGGER.warning(
                            f"No deals data found for account {broker_account_id}"
                        )
                        return None

                    deals_list = deals_dict.get("deals", [])
                    available_cash = Money(
                        Decimal(str(balance_dict.get("availableCash", 0)))
                    )
                    net_asset_value = Money(
                        Decimal(str(balance_dict.get("netAssetValue", 0)))
                    )

                    # Process current deals into portfolio positions
                    current_positions = PortfolioProcessor.process_deals_to_positions(
                        deals_list, float(net_asset_value.amount)
                    )

                    # Get target portfolio weights
                    current_date = TimeUtils.get_current_vn_time()
                    last_trading_date = self.trading_calendar.get_last_trading_date(
                        current_date
                    )
                    last_trading_date_str = last_trading_date.strftime(
                        SQLServerConsts.DATE_FORMAT
                    )

                    portfolio_data = (
                        await self.portfolio_data_provider.get_portfolio_weights(
                            last_trading_date=last_trading_date_str,
                            current_date=current_date.strftime(
                                SQLServerConsts.DATE_FORMAT
                            ),
                        )
                    )

                    if not portfolio_data:
                        LOGGER.warning(
                            f"No portfolio weights found for {last_trading_date_str}"
                        )
                        return None

                    # Get target weights based on strategy
                    strategy = StrategyFactory.create_strategy(strategy_type)
                    target_weights = strategy.get_target_weights(portfolio_data)

                    # Generate recommendations
                    recommendations = (
                        self.recommendation_engine.generate_recommendations(
                            current_positions=current_positions,
                            target_weights=target_weights,
                            available_cash=available_cash,
                            net_asset_value=net_asset_value,
                        )
                    )

                    return {
                        "account_id": broker_account_id,
                        "strategy_type": strategy_type,
                        "account_balance": {
                            "available_cash": float(available_cash.amount),
                            "net_asset_value": float(net_asset_value.amount),
                            "cash_ratio": (
                                (available_cash.amount / net_asset_value.amount * 100)
                                if net_asset_value.amount > 0
                                else 0
                            ),
                        },
                        "current_positions": current_positions,
                        "target_weights": target_weights,
                        "recommendations": recommendations,
                        "analysis_date": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                    }

        except Exception as e:
            LOGGER.error(f"Error analyzing portfolio for user {user.userId}: {e}")
            return None

    async def generate_portfolio_report(
        self,
        user: JwtPayload,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
        include_trade_plan: bool = True,
    ) -> Optional[str]:
        """Generate a formatted portfolio report"""
        try:
            analysis = await self.analyze_portfolio(
                user=user,
                broker_account_id=broker_account_id,
                strategy_type=strategy_type,
            )

            if not analysis:
                return "❌ Không thể phân tích danh mục đầu tư"

            return PortfolioReportGenerator.generate_text_report(
                account_id=analysis["account_id"],
                strategy_type=analysis["strategy_type"],
                positions=analysis["current_positions"],
                recommendations=analysis["recommendations"],
                account_balance=analysis["account_balance"],
                analysis_date=analysis["analysis_date"],
                include_trade_plan=include_trade_plan,
            )

        except Exception as e:
            LOGGER.error(
                f"Error generating portfolio report for user {user.userId}: {e}"
            )
            return f"❌ Lỗi tạo báo cáo: {str(e)}"


# Notification Service
class PortfolioNotificationService:
    def __init__(
        self,
        portfolio_data_provider: PortfolioDataProvider = None,
        trading_calendar: TradingCalendarService = None,
    ):
        self.portfolio_data_provider = (
            portfolio_data_provider or PortfolioDataProvider()
        )
        self.trading_calendar = trading_calendar or TradingCalendarService()

    async def send_daily_portfolio_notification(self):
        """Send daily portfolio notification to all users"""
        try:
            current_date = TimeUtils.get_current_vn_time()

            # Check if today is a trading day
            if not self.trading_calendar.is_trading_day(current_date):
                LOGGER.info(
                    f"Today ({current_date.strftime('%A %d/%m/%Y')}) is not a trading day. Skipping notification."
                )
                return

            # Get last trading date
            last_trading_date = self.trading_calendar.get_last_trading_date(
                current_date
            )
            last_trading_date_str = last_trading_date.strftime(
                SQLServerConsts.DATE_FORMAT
            )
            current_date_str = current_date.strftime(SQLServerConsts.DATE_FORMAT)

            LOGGER.info(
                f"Sending daily portfolio notification for {last_trading_date_str}"
            )

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            if not notification_service.is_ready():
                LOGGER.error("Notification service not available")
                return

            # Get portfolio data
            portfolio_data = await self.portfolio_data_provider.get_portfolio_weights(
                last_trading_date_str, current_date_str
            )

            if not portfolio_data:
                await notify_error(
                    "KHÔNG CÓ DỮ LIỆU DANH MỤC",
                    f"Không tìm thấy dữ liệu danh mục cho ngày {last_trading_date.strftime('%d/%m/%Y')}",
                )
                return

            # Notify about daily portfolio weights
            await notification_service.notify_daily_portfolio(
                portfolio_data=portfolio_data
            )
            LOGGER.info("Daily portfolio notification sent successfully")

        except Exception as e:
            LOGGER.error(f"Error in daily portfolio notification: {e}")
            await notify_error(
                "LỖI THÔNG BÁO DANH MỤC",
                f"Có lỗi khi gửi thông báo danh mục hàng ngày: {str(e)}",
            )

    async def send_test_notification(self, date: Optional[str] = None):
        """Send test portfolio notification"""
        try:
            if date is None:
                current_date = TimeUtils.get_current_vn_time()
                last_trading_date = self.trading_calendar.get_last_trading_date(
                    current_date
                )
                date = last_trading_date.strftime("%Y-%m-%d")
                current_date_str = current_date.strftime(SQLServerConsts.DATE_FORMAT)

            LOGGER.info(f"Sending test portfolio notification for {date}")

            # Initialize notification service
            if not notification_service.is_ready():
                await notification_service.initialize()

            # Get and send portfolio data
            portfolio_data = await self.portfolio_data_provider.get_portfolio_weights(
                last_trading_date=date, current_date=current_date_str
            )

            if portfolio_data:
                await notification_service.notify_daily_portfolio(
                    portfolio_data=portfolio_data
                )
                print(f"✅ Test notification sent for {date}")
            else:
                print(f"❌ No portfolio data found for {date}")

        except Exception as e:
            print(f"❌ Error sending test notification: {e}")
            LOGGER.error(f"Error in test notification: {e}")


# Scheduler Service
class PortfolioSchedulerService:
    def __init__(self, notification_service: PortfolioNotificationService = None):
        self.notification_service = (
            notification_service or PortfolioNotificationService()
        )

    def schedule_daily_notifications(self):
        """Schedule daily notifications"""
        notification_time = "07:30" if os.getenv("TEST") == "1" else "00:00"
        schedule.every().day.at(notification_time).do(
            lambda: asyncio.create_task(
                self.notification_service.send_daily_portfolio_notification()
            )
        )
        LOGGER.info(f"Daily portfolio notifications scheduled for {notification_time}")

    async def run_scheduler(self):
        """Run the notification scheduler"""
        self.schedule_daily_notifications()
        LOGGER.info("Portfolio notification scheduler started")

        while True:
            schedule.run_pending()
            print(
                f"Scheduler running at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await asyncio.sleep(60)  # Check every minute


# Legacy Facade (Backward Compatibility)
class DailyPortfolioNotificationService:
    """
    Legacy facade to maintain backward compatibility.
    New code should use the individual services directly.
    """

    def __init__(self):
        self.analysis_service = PortfolioAnalysisService()
        self.notification_service = PortfolioNotificationService()
        self.scheduler_service = PortfolioSchedulerService()
        self.trading_calendar = TradingCalendarService()
        self.portfolio_data_provider = PortfolioDataProvider()

        # Legacy compatibility
        self.repo = OptimizedWeightsRepo

    # Legacy methods for backward compatibility
    @classmethod
    def is_trading_day(cls, date: datetime) -> bool:
        return TradingCalendarService.is_trading_day(date)

    @classmethod
    def get_last_trading_date(cls, current_date: datetime) -> datetime:
        return TradingCalendarService.get_last_trading_date(current_date)

    async def get_portfolio_weights(
        self, last_trading_date: str, current_date: str
    ) -> Optional[Dict]:
        return await self.portfolio_data_provider.get_portfolio_weights(
            last_trading_date, current_date
        )

    async def send_daily_portfolio_notification(self):
        return await self.notification_service.send_daily_portfolio_notification()

    async def analyze_portfolio_and_recommend(
        self,
        user: JwtPayload,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
    ) -> Optional[Dict]:
        return await self.analysis_service.analyze_portfolio(
            user, broker_account_id, strategy_type
        )

    async def generate_portfolio_report(
        self,
        user: JwtPayload,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
        include_trade_plan: bool = True,
    ) -> Optional[str]:
        return await self.analysis_service.generate_portfolio_report(
            user, broker_account_id, strategy_type, include_trade_plan
        )

    def schedule_daily_notifications(self):
        return self.scheduler_service.schedule_daily_notifications()

    async def run_scheduler(self):
        return await self.scheduler_service.run_scheduler()

    async def send_test_notification(self, date: Optional[str] = None):
        return await self.notification_service.send_test_notification(date)

    # Deprecated methods - use new services instead
    @classmethod
    def process_current_deals(
        cls, deals_list: List[Dict], net_asset_value: float
    ) -> List[Dict]:
        """Deprecated: Use PortfolioProcessor.process_deals_to_positions instead"""
        positions = PortfolioProcessor.process_deals_to_positions(
            deals_list, net_asset_value
        )
        # Convert back to old format for compatibility
        return [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "market_price": float(pos.market_price.amount),
                "market_value": float(pos.market_value.amount),
                "weight_pct": float(pos.weight.percentage),
                "cost_price": float(pos.cost_price.amount),
                "unrealized_profit": (
                    float(pos.unrealized_profit.amount) if pos.unrealized_profit else 0
                ),
            }
            for pos in positions
        ]

    @classmethod
    def generate_trade_recommendations(
        cls,
        current_portfolio: List[Dict],
        target_weights: List[Dict],
        available_cash: float,
        net_asset_value: float,
        strategy_type: str,
        weight_tolerance: float = 2.0,
    ) -> Dict:
        """Deprecated: Use RecommendationEngine.generate_recommendations instead"""
        # Convert old format to new format
        positions = []
        for pos_dict in current_portfolio:
            position = Position(
                symbol=pos_dict["symbol"],
                quantity=pos_dict["quantity"],
                market_price=Money(Decimal(str(pos_dict["market_price"]))),
                cost_price=Money(Decimal(str(pos_dict.get("cost_price", 0)))),
                weight=Weight(Decimal(str(pos_dict["weight_pct"]))),
                unrealized_profit=Money(
                    Decimal(str(pos_dict.get("unrealized_profit", 0)))
                ),
            )
            positions.append(position)

        engine = RecommendationEngine(weight_tolerance)
        recommendations = engine.generate_recommendations(
            current_positions=positions,
            target_weights=target_weights,
            available_cash=Money(Decimal(str(available_cash))),
            net_asset_value=Money(Decimal(str(net_asset_value))),
        )

        # Convert back to old format
        buy_recs = []
        sell_recs = []
        total_required_cash = 0

        for rec in recommendations:
            rec_dict = {
                "symbol": rec.symbol,
                "action": rec.action,
                "current_weight": float(rec.current_weight.percentage),
                "target_weight": float(rec.target_weight.percentage),
                "weight_difference": float(
                    rec.target_weight.percentage - rec.current_weight.percentage
                ),
                "priority": rec.priority,
            }

            if rec.action == "BUY":
                rec_dict.update(
                    {
                        "current_value": 0,  # Would need to calculate
                        "target_value": 0,  # Would need to calculate
                        "cash_needed": float(rec.amount.amount),
                    }
                )
                buy_recs.append(rec_dict)
                total_required_cash += float(rec.amount.amount)
            else:
                rec_dict.update(
                    {
                        "current_value": 0,  # Would need to calculate
                        "target_value": 0,  # Would need to calculate
                        "cash_to_raise": float(rec.amount.amount),
                        "current_quantity": 0,  # Would need to calculate
                    }
                )
                sell_recs.append(rec_dict)

        return {
            "buy_recommendations": buy_recs,
            "sell_recommendations": sell_recs,
            "rebalance_recommendations": [],
            "summary": {
                "total_recommendations": len(recommendations),
                "required_cash": total_required_cash,
                "available_cash": available_cash,
                "cash_sufficient": available_cash >= total_required_cash,
                "cash_utilization": (
                    (total_required_cash / available_cash * 100)
                    if available_cash > 0
                    else 0
                ),
            },
        }

    async def get_detailed_trade_plan(
        self,
        user: JwtPayload,
        broker_account_id: str,
        strategy_type: str = "long_only",
        max_positions: int = 10,
    ) -> Optional[Dict]:
        """Deprecated: Use new services instead"""
        # Simplified implementation for backward compatibility
        analysis = await self.analyze_portfolio_and_recommend(
            user, broker_account_id, strategy_type
        )
        if not analysis:
            return None

        # Basic trade plan structure
        return {
            "account_id": broker_account_id,
            "strategy": strategy_type,
            "execution_date": TimeUtils.get_current_vn_time().strftime("%Y-%m-%d"),
            "account_summary": analysis["account_balance"],
            "sell_orders": [],
            "buy_orders": [],
            "execution_summary": {
                "total_sell_value": 0,
                "total_buy_value": 0,
                "net_cash_flow": 0,
                "feasible": True,
                "warnings": [],
                "timing_suggestion": "Execute during trading hours",
            },
        }
