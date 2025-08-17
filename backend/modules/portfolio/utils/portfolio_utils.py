import re
import datetime
from typing import Dict, Any, Optional, Union

from backend.common.consts import SQLServerConsts
from backend.modules.portfolio.infrastructure import TradingCalendarService


class PortfolioUtils:
    @staticmethod
    def generate_general_portfolio_id(date: str = None) -> str:
        if not date:
            last_trading_date, _ = TradingCalendarService.get_last_next_trading_dates()
            date = last_trading_date.strftime(SQLServerConsts.DATE_FORMAT)
        year_month = date[:7]
        return f"SYSTEM-{year_month}"
    
    @staticmethod 
    def generate_custom_portfolio_id(user_id: int, portfolio_name: str) -> str:
        import uuid
        unique_id = str(uuid.uuid4())[:8].upper()
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', portfolio_name)[:10].upper()
        return f"CUSTOM-{user_id}-{safe_name}-{unique_id}"
    
    @staticmethod
    def parse_portfolio_id(portfolio_id: str) -> Dict[str, Any]:
        parts = portfolio_id.split('_')
        
        if parts[0] == 'SYSTEM':
            return {
                'type': 'SYSTEM',
                'year_month': parts[1] if len(parts) > 1 else None
            }
        elif parts[0] == 'CUSTOM':
            return {
                'type': 'USER-CUSTOM', 
                'user_id': int(parts[1]) if len(parts) > 1 else None,
                'name_part': parts[2] if len(parts) > 2 else None,
                'unique_id': parts[3] if len(parts) > 3 else None
            }
        
        return {'type': 'UNKNOWN'}