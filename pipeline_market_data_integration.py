# =====================================================
# TRADING BOT PIPELINE ARCHITECTURE
# =====================================================

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, time, timedelta
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from fastapi import FastAPI, BackgroundTasks
import redis
from celery import Celery
from apscheduler.schedulers.asyncio import AsyncIOScheduler


# =====================================================
# PIPELINE CONFIGURATION
# =====================================================

class PipelineStage(Enum):
    MARKET_DATA_COLLECTION = "market_data_collection"
    DATA_VALIDATION = "data_validation"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    RISK_ASSESSMENT = "risk_assessment"
    ORDER_GENERATION = "order_generation"
    ORDER_EXECUTION = "order_execution"
    POSITION_UPDATE = "position_update"
    PERFORMANCE_TRACKING = "performance_tracking"


@dataclass
class PipelineConfig:
    trading_start_time: time = time(9, 0)  # 9:00 AM
    trading_end_time: time = time(15, 0)  # 3:00 PM
    portfolio_update_time: time = time(8, 30)  # 8:30 AM
    risk_check_interval: int = 300  # 5 minutes
    market_data_interval: int = 60  # 1 minute
    max_retry_attempts: int = 3
    pipeline_timeout: int = 1800  # 30 minutes


# =====================================================
# MAIN TRADING PIPELINE
# =====================================================

class TradingPipeline:
    """Main trading pipeline orchestrator"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.scheduler = AsyncIOScheduler()
        self.redis_client = redis.Redis()

        # Initialize components
        self.market_data_service = MarketDataService()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_manager = RiskManager()
        self.order_manager = OrderManager()
        self.broker_client = DNSEBrokerClient()

        # Pipeline state
        self.is_running = False
        self.current_stage = None
        self.pipeline_metrics = {}

    async def start_pipeline(self):
        """Start the trading pipeline with scheduled jobs"""
        self.is_running = True
        self.logger.info("Starting trading pipeline...")

        # Schedule daily portfolio optimization
        self.scheduler.add_job(
            self.run_daily_pipeline,
            'cron',
            hour=self.config.portfolio_update_time.hour,
            minute=self.config.portfolio_update_time.minute,
            id='daily_portfolio_update'
        )

        # Schedule intraday risk monitoring
        self.scheduler.add_job(
            self.run_risk_monitoring,
            'interval',
            seconds=self.config.risk_check_interval,
            id='risk_monitoring'
        )

        # Schedule market data collection
        self.scheduler.add_job(
            self.collect_market_data,
            'interval',
            seconds=self.config.market_data_interval,
            id='market_data_collection'
        )

        # Schedule end-of-day processing
        self.scheduler.add_job(
            self.run_eod_processing,
            'cron',
            hour=self.config.trading_end_time.hour,
            minute=self.config.trading_end_time.minute + 30,
            id='eod_processing'
        )

        self.scheduler.start()
        self.logger.info("Trading pipeline started successfully")

    async def run_daily_pipeline(self):
        """Run complete daily trading pipeline"""
        pipeline_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            self.logger.info(f"Starting daily pipeline: {pipeline_id}")

            # Stage 1: Market Data Collection
            await self._execute_stage(
                PipelineStage.MARKET_DATA_COLLECTION,
                self.collect_eod_data,
                pipeline_id
            )

            # Stage 2: Data Validation
            await self._execute_stage(
                PipelineStage.DATA_VALIDATION,
                self.validate_market_data,
                pipeline_id
            )

            # Stage 3: Portfolio Optimization
            await self._execute_stage(
                PipelineStage.PORTFOLIO_OPTIMIZATION,
                self.optimize_portfolios,
                pipeline_id
            )

            # Stage 4: Risk Assessment
            await self._execute_stage(
                PipelineStage.RISK_ASSESSMENT,
                self.assess_portfolio_risks,
                pipeline_id
            )

            # Stage 5: Order Generation
            await self._execute_stage(
                PipelineStage.ORDER_GENERATION,
                self.generate_rebalancing_orders,
                pipeline_id
            )

            # Stage 6: Order Execution
            await self._execute_stage(
                PipelineStage.ORDER_EXECUTION,
                self.execute_orders,
                pipeline_id
            )

            self.logger.info(f"Daily pipeline completed: {pipeline_id}")

        except Exception as e:
            self.logger.error(f"Daily pipeline failed: {pipeline_id}, Error: {str(e)}")
            await self._handle_pipeline_failure(pipeline_id, e)

    async def _execute_stage(self, stage: PipelineStage, func, pipeline_id: str):
        """Execute a pipeline stage with error handling and metrics"""
        stage_start = datetime.now()
        self.current_stage = stage

        try:
            self.logger.info(f"Executing stage: {stage.value}")
            result = await func()

            # Record metrics
            duration = (datetime.now() - stage_start).total_seconds()
            self.pipeline_metrics[stage.value] = {
                'status': 'success',
                'duration': duration,
                'timestamp': stage_start,
                'result': result
            }

        except Exception as e:
            duration = (datetime.now() - stage_start).total_seconds()
            self.pipeline_metrics[stage.value] = {
                'status': 'failed',
                'duration': duration,
                'timestamp': stage_start,
                'error': str(e)
            }
            raise

    async def collect_eod_data(self):
        """Collect end-of-day market data"""
        return await self.market_data_service.collect_eod_data()

    async def validate_market_data(self):
        """Validate collected market data"""
        return await self.market_data_service.validate_data()

    async def optimize_portfolios(self):
        """Run portfolio optimization for all active portfolios"""
        return await self.portfolio_optimizer.optimize_all_portfolios()

    async def assess_portfolio_risks(self):
        """Assess risk metrics for all portfolios"""
        return await self.risk_manager.assess_all_portfolios()

    async def generate_rebalancing_orders(self):
        """Generate orders for portfolio rebalancing"""
        return await self.order_manager.generate_rebalancing_orders()

    async def execute_orders(self):
        """Execute generated orders through broker"""
        return await self.order_manager.execute_pending_orders()


# =====================================================
# MARKET DATA SERVICE
# =====================================================

class MarketDataService:
    """Service for collecting and managing market data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dnse_client = DNSEMarketDataClient()
        self.data_validator = MarketDataValidator()

    async def collect_eod_data(self) -> Dict[str, Any]:
        """Collect end-of-day data for all active assets"""
        try:
            # Get list of active assets
            active_assets = await self._get_active_assets()

            # Collect EOD data
            eod_data = {}
            for asset in active_assets:
                try:
                    data = await self.dnse_client.get_eod_data(asset['symbol'])
                    eod_data[asset['symbol']] = data
                except Exception as e:
                    self.logger.error(f"Failed to collect data for {asset['symbol']}: {str(e)}")

            # Store in database
            await self._store_eod_data(eod_data)

            return {
                'collected_assets': len(eod_data),
                'total_assets': len(active_assets),
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"EOD data collection failed: {str(e)}")
            raise

    async def collect_intraday_data(self) -> Dict[str, Any]:
        """Collect real-time intraday data"""
        try:
            active_assets = await self._get_active_assets()

            # Collect real-time quotes
            quotes = {}
            for asset in active_assets:
                try:
                    quote = await self.dnse_client.get_real_time_quote(asset['symbol'])
                    quotes[asset['symbol']] = quote
                except Exception as e:
                    self.logger.warning(f"Failed to get quote for {asset['symbol']}: {str(e)}")

            # Store in database
            await self._store_intraday_data(quotes)

            return {
                'collected_quotes': len(quotes),
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Intraday data collection failed: {str(e)}")
            raise

    async def validate_data(self) -> Dict[str, Any]:
        """Validate collected market data"""
        return await self.data_validator.validate_latest_data()


# =====================================================
# DNSE BROKER INTEGRATION
# =====================================================

class DNSEBrokerClient:
    """DNSE Broker API integration"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.dnse.com.vn"
        self.api_key = os.getenv('DNSE_API_KEY')
        self.secret_key = os.getenv('DNSE_SECRET_KEY')
        self.session = aiohttp.ClientSession()

    async def authenticate(self) -> str:
        """Authenticate with DNSE API and get access token"""
        try:
            auth_data = {
                'api_key': self.api_key,
                'secret_key': self.secret_key,
                'timestamp': int(datetime.now().timestamp())
            }

            # Create signature
            signature = self._create_signature(auth_data)
            auth_data['signature'] = signature

            async with self.session.post(f"{self.base_url}/auth/token", json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['access_token']
                else:
                    raise Exception(f"Authentication failed: {response.status}")

        except Exception as e:
            self.logger.error(f"DNSE authentication failed: {str(e)}")
            raise

    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            token = await self.authenticate()
            headers = {'Authorization': f'Bearer {token}'}

            async with self.session.get(f"{self.base_url}/account/info", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get account info: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get account info: {str(e)}")
            raise

    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place trading order"""
        try:
            token = await self.authenticate()
            headers = {'Authorization': f'Bearer {token}'}

            # Validate order data
            validated_order = self._validate_order_data(order_data)

            async with self.session.post(
                    f"{self.base_url}/orders/place",
                    json=validated_order,
                    headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Order placed successfully: {result['order_id']}")
                    return result
                else:
                    error_text = await response.text()
                    raise Exception(f"Order placement failed: {response.status}, {error_text}")

        except Exception as e:
            self.logger.error(f"Failed to place order: {str(e)}")
            raise

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel existing order"""
        try:
            token = await self.authenticate()
            headers = {'Authorization': f'Bearer {token}'}

            async with self.session.delete(
                    f"{self.base_url}/orders/{order_id}",
                    headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Order cancelled: {order_id}")
                    return result
                else:
                    raise Exception(f"Order cancellation failed: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status"""
        try:
            token = await self.authenticate()
            headers = {'Authorization': f'Bearer {token}'}

            async with self.session.get(
                    f"{self.base_url}/orders/{order_id}",
                    headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get order status: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get order status {order_id}: {str(e)}")
            raise

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        try:
            token = await self.authenticate()
            headers = {'Authorization': f'Bearer {token}'}

            async with self.session.get(f"{self.base_url}/portfolio/positions", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to get positions: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get positions: {str(e)}")
            raise

    def _create_signature(self, data: Dict[str, Any]) -> str:
        """Create API signature for authentication"""
        import hmac
        import hashlib

        # Sort parameters
        sorted_params = sorted(data.items())
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])

        # Create signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _validate_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data before sending"""
        required_fields = ['symbol', 'side', 'quantity', 'order_type']

        for field in required_fields:
            if field not in order_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate order type
        valid_order_types = ['MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT']
        if order_data['order_type'] not in valid_order_types:
            raise ValueError(f"Invalid order type: {order_data['order_type']}")

        # Validate side
        valid_sides = ['BUY', 'SELL']
        if order_data['side'] not in valid_sides:
            raise ValueError(f"Invalid side: {order_data['side']}")

        return order_data


class DNSEMarketDataClient:
    """DNSE Market Data API client"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.dnse.com.vn"
        self.session = aiohttp.ClientSession()

    async def get_eod_data(self, symbol: str, date: str = None) -> Dict[str, Any]:
        """Get end-of-day data for a symbol"""
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            url = f"{self.base_url}/market-data/eod/{symbol}"
            params = {'date': date}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': symbol,
                        'date': date,
                        'open': data['open'],
                        'high': data['high'],
                        'low': data['low'],
                        'close': data['close'],
                        'volume': data['volume'],
                        'adjusted_close': data.get('adjusted_close', data['close'])
                    }
                else:
                    raise Exception(f"Failed to get EOD data for {symbol}: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get EOD data for {symbol}: {str(e)}")
            raise

    async def get_real_time_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        try:
            url = f"{self.base_url}/market-data/quote/{symbol}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': symbol,
                        'price': data['last_price'],
                        'bid_price': data['bid_price'],
                        'ask_price': data['ask_price'],
                        'bid_size': data['bid_size'],
                        'ask_size': data['ask_size'],
                        'volume': data['volume'],
                        'timestamp': datetime.now()
                    }
                else:
                    raise Exception(f"Failed to get quote for {symbol}: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get quote for {symbol}: {str(e)}")
            raise

    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get historical data for a symbol"""
        try:
            url = f"{self.base_url}/market-data/historical/{symbol}"
            params = {
                'start_date': start_date,
                'end_date': end_date
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']
                else:
                    raise Exception(f"Failed to get historical data for {symbol}: {response.status}")

        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {str(e)}")
            raise


# =====================================================
# ORDER MANAGEMENT SYSTEM
# =====================================================

class OrderManager:
    """Manage order lifecycle and execution"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.broker_client = DNSEBrokerClient()
        self.db_session = get_db_session()

    async def generate_rebalancing_orders(self) -> Dict[str, Any]:
        """Generate orders for portfolio rebalancing"""
        try:
            # Get all active portfolios
            active_portfolios = await self._get_active_portfolios()

            total_orders = 0
            generated_orders = []

            for portfolio in active_portfolios:
                orders = await self._generate_portfolio_orders(portfolio)
                generated_orders.extend(orders)
                total_orders += len(orders)

            # Store orders in database
            await self._store_orders(generated_orders)

            return {
                'total_orders_generated': total_orders,
                'portfolios_processed': len(active_portfolios),
                'timestamp': datetime.now()
            }

        except Exception as e:
            self.logger.error(f"Failed to generate rebalancing orders: {str(e)}")
            raise

    async def _generate_portfolio_orders(self, portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate orders for a specific portfolio"""
        try:
            # Get current positions
            current_positions = await self._get_current_positions(portfolio['id'])

            # Get target weights
            target_weights = await self._get_latest_target_weights(portfolio['id'])

            # Calculate required trades
            orders = []
            portfolio_value = portfolio['current_value']

            for asset_symbol, target_weight in target_weights.items():
                current_position = current_positions.get(asset_symbol, {'quantity': 0, 'market_value': 0})
                current_weight = current_position['market_value'] / portfolio_value if portfolio_value > 0 else 0

                weight_diff = target_weight - current_weight

                # Only trade if difference is significant
                if abs(weight_diff) > 0.01:  # 1% threshold
                    target_value = target_weight * portfolio_value
                    current_value = current_position['market_value']
                    trade_value = target_value - current_value

                    # Get current price
                    current_price = await self._get_current_price(asset_symbol)

                    if current_price > 0:
                        quantity = int(trade_value / current_price)

                        if abs(quantity) > 0:
                            order = {
                                'portfolio_id': portfolio['id'],
                                'symbol': asset_symbol,
                                'side': 'BUY' if quantity > 0 else 'SELL',
                                'quantity': abs(quantity),
                                'order_type': 'MARKET',
                                'time_in_force': 'DAY',
                                'reason': 'REBALANCING'
                            }
                            orders.append(order)

            return orders

        except Exception as e:
            self.logger.error(f"Failed to generate orders for portfolio {portfolio['id']}: {str(e)}")
            return []

    async def execute_pending_orders(self) -> Dict[str, Any]:
        """Execute all pending orders"""
        try:
            # Get pending orders
            pending_orders = await self._get_pending_orders()

            execution_results = {
                'successful': 0,
                'failed': 0,
                'total': len(pending_orders)
            }

            for order in pending_orders:
                try:
                    # Execute order through broker
                    broker_response = await self.broker_client.place_order({
                        'symbol': order['symbol'],
                        'side': order['side'],
                        'quantity': order['quantity'],
                        'order_type': order['order_type'],
                        'time_in_force': order['time_in_force']
                    })

                    # Update order status
                    await self._update_order_status(
                        order['id'],
                        'SUBMITTED',
                        broker_response['order_id']
                    )

                    execution_results['successful'] += 1

                except Exception as e:
                    self.logger.error(f"Failed to execute order {order['id']}: {str(e)}")

                    # Update order status as failed
                    await self._update_order_status(
                        order['id'],
                        'REJECTED',
                        None,
                        str(e)
                    )

                    execution_results['failed'] += 1

            return execution_results

        except Exception as e:
            self.logger.error(f"Failed to execute pending orders: {str(e)}")
            raise

    async def monitor_order_status(self) -> Dict[str, Any]:
        """Monitor status of submitted orders"""
        try:
            # Get submitted orders
            submitted_orders = await self._get_submitted_orders()

            status_updates = {
                'filled': 0,
                'cancelled': 0,
                'pending': 0
            }

            for order in submitted_orders:
                try:
                    # Check order status with broker
                    broker_status = await self.broker_client.get_order_status(order['broker_order_id'])

                    if broker_status['status'] != order['status']:
                        # Update order status
                        await self._update_order_status(
                            order['id'],
                            broker_status['status'],
                            order['broker_order_id'],
                            filled_quantity=broker_status.get('filled_quantity'),
                            filled_price=broker_status.get('filled_price')
                        )

                        # Update position if filled
                        if broker_status['status'] == 'FILLED':
                            await self._update_position_from_fill(order, broker_status)
                            status_updates['filled'] += 1
                        elif broker_status['status'] == 'CANCELLED':
                            status_updates['cancelled'] += 1
                        else:
                            status_updates['pending'] += 1

                except Exception as e:
                    self.logger.error(f"Failed to check status for order {order['id']}: {str(e)}")

            return status_updates

        except Exception as e:
            self.logger.error(f"Failed to monitor order status: {str(e)}")
            raise


# =====================================================
# REQUIREMENTS.TXT & FRAMEWORK SETUP
# =====================================================

REQUIREMENTS = """
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.13.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Data Processing
pandas==2.1.4
numpy==1.25.2
scipy==1.11.4
scikit-learn==1.3.2

# Trading & Finance
yfinance==0.2.28
ta==0.10.2
quantlib==1.32

# Async & Concurrency
aiohttp==3.9.1
asyncio-mqtt==0.13.0
celery==5.3.4
redis==5.0.1

# Scheduling
apscheduler==3.10.4
croniter==2.0.1

# Monitoring & Observability
prometheus-client==0.19.0
structlog==23.2.0
sentry-sdk==1.38.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
httpx==0.25.2

# Development
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1

# Security
cryptography==41.0.8
passlib==1.7.4
python-jose==3.3.0

# Configuration
python-dotenv==1.0.0
pyyaml==6.0.1

# Deployment
gunicorn==21.2.0
docker==6.1.3
kubernetes==28.1.0
"""


# =====================================================
# MAIN APPLICATION SETUP
# =====================================================

class TradingBotApplication:
    """Main application class"""

    def __init__(self):
        self.app = FastAPI(title="Trading Bot API", version="1.0.0")
        self.pipeline = None
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """Setup FastAPI middleware"""
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.gzip import GZipMiddleware

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

    def setup_routes(self):
        """Setup API routes"""
        from src.api.routers import portfolio, orders, market_data, monitoring

        self.app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["portfolio"])
        self.app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
        self.app.include_router(market_data.router, prefix="/api/v1/market-data", tags=["market-data"])
        self.app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])

    async def startup(self):
        """Application startup"""
        # Initialize database
        from src.database.connection import init_database
        await init_database()

        # Start trading pipeline
        config = PipelineConfig()
        self.pipeline = TradingPipeline(config)
        await self.pipeline.start_pipeline()

        logging.info("Trading bot application started successfully")

    async def shutdown(self):
        """Application shutdown"""
        if self.pipeline:
            self.pipeline.scheduler.shutdown()

        logging.info("Trading bot application shut down")


# Application instance
app = TradingBotApplication()


@app.app.on_event("startup")
async def startup_event():
    await app.startup()


@app.app.on_event("shutdown")
async def shutdown_event():
    await app.shutdown()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app.app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )