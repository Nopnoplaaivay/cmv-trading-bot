from typing import Dict, List, Optional
from decimal import Decimal

from backend.common.consts import SQLServerConsts, MessageConsts
from backend.common.responses.exceptions.base_exceptions import BaseExceptionResponse
from backend.modules.auth.types import JwtPayload
from backend.modules.dnse.trading_session import TradingSession
from backend.modules.portfolio.core import Position, Money, Weight
from backend.modules.portfolio.core.strategies import StrategyFactory
from backend.modules.portfolio.services.processors import (
    PortfolioProcessor,
    RecommendationEngine,
)
from backend.modules.portfolio.services.data_providers import (
    PortfolioDataProvider,
    AccountDataProvider,
)
from backend.modules.portfolio.infrastructure import TradingCalendarService
from backend.utils.logger import LOGGER
from backend.utils.time_utils import TimeUtils
from backend.utils.json_utils import JSONUtils


LOGGER_PREFIX = "[PortfolioAnalysis]"


# Main Portfolio Analysis Service
class PortfolioAnalysisService:
    portfolio_data_provider = PortfolioDataProvider
    account_data_provider = AccountDataProvider
    recommendation_engine = RecommendationEngine()
    trading_calendar = TradingCalendarService

    @classmethod
    async def analyze_system_portfolio(
        cls,
        broker_account_id: str,
        strategy_type: str = "market_neutral",
    ) -> Optional[Dict]:
        try:
            LOGGER.info(f"{LOGGER_PREFIX} Analyzing portfolio for account {broker_account_id}")

            # Get account details
            trade_account = await cls.account_data_provider.get_trading_account(
                broker_account_id
            )
            if not trade_account:
                LOGGER.warning(
                    f"{LOGGER_PREFIX} No trading account found for broker_account_id: {broker_account_id}"
                )
                return None

            custody_code = trade_account.get("custodyCode")
            password = trade_account.get("password")

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
                            f"{LOGGER_PREFIX} No balance data found for account {broker_account_id}"
                        )
                        return None

                    if not deals_dict:
                        LOGGER.warning(
                            f"{LOGGER_PREFIX} No deals data found for account {broker_account_id}"
                        )
                        return None

                    deals_list = deals_dict.get("deals", [])
                    available_cash = Money(
                        Decimal(str(balance_dict.get("availableCash", 0)))
                    )
                    net_asset_value = Money(
                        Decimal(str(balance_dict.get("netAssetValue", 0)))
                    )
                    stock_value = Money(Decimal(str(balance_dict.get("stockValue", 0))))

                    # Process current deals into portfolio positions
                    current_positions = PortfolioProcessor.process_deals_to_positions(
                        deals_list,
                        float(net_asset_value.amount),
                        float(stock_value.amount),
                    )

                    # Get target portfolio weights
                    last_trading_date, next_trading_date = (
                        cls.trading_calendar.get_last_next_trading_dates()
                    )

                    last_trading_date_str = last_trading_date.strftime(
                        SQLServerConsts.DATE_FORMAT
                    )
                    next_trading_date_str = next_trading_date.strftime(
                        SQLServerConsts.DATE_FORMAT
                    )

                    LOGGER.info(
                        f"{LOGGER_PREFIX} Sending daily portfolio notification for {next_trading_date_str}"
                    )

                    portfolio_data = (
                        await cls.portfolio_data_provider.get_system_portfolio(
                            last_trading_date=last_trading_date_str,
                            next_trading_date=next_trading_date_str,
                        )
                    )

                    if not portfolio_data:
                        LOGGER.warning(
                            f"{LOGGER_PREFIX} No portfolio weights found for {next_trading_date_str}"
                        )
                        return None

                    # Get target weights based on strategy: long only or market neutral
                    strategy = StrategyFactory.create_strategy(strategy_type)
                    target_weights = strategy.get_target_weights(portfolio_data)

                    # Generate recommendations
                    recommendations = (
                        cls.recommendation_engine.generate_recommendations(
                            current_positions=current_positions,
                            target_weights=target_weights,
                            available_cash=available_cash,
                            net_asset_value=net_asset_value,
                        )
                    )

                    result = {
                        "account_id": broker_account_id,
                        "strategy_type": strategy_type,
                        "account_balance": {
                            "available_cash": float(available_cash.amount),
                            "net_asset_value": float(net_asset_value.amount),
                            "cash_ratio": float(
                                (available_cash.amount / net_asset_value.amount * 100)
                                if net_asset_value.amount > 0
                                else 0
                            ),
                        },
                        "current_positions": [
                            pos.to_dict() for pos in current_positions
                        ],
                        "target_weights": target_weights,
                        "recommendations": [rec.to_dict() for rec in recommendations],
                        "analysis_date": (
                            next_trading_date.strftime(SQLServerConsts.DATE_FORMAT)
                            if next_trading_date
                            else TimeUtils.get_current_vn_time().strftime(
                                SQLServerConsts.DATE_FORMAT
                            )
                        ),
                    }

                    serializable_result = JSONUtils.make_json_serializable(result)
                    return serializable_result

        except Exception as e:
            LOGGER.error(
                f"{LOGGER_PREFIX} Error in portfolio analysis for account {broker_account_id}: {str(e)}"
            )
            raise BaseExceptionResponse(
                http_code=500,
                status_code=500,
                message=MessageConsts.INTERNAL_SERVER_ERROR,
                errors=str(e),
            )

