from typing import Dict, Any, Optional, Union
import re


class PortfolioUtils:
    @staticmethod
    def generate_general_portfolio_id(date: str) -> str:
        year_month = date[:7]  # "2024-12"
        return f"GENERAL-{year_month}"
    
    @staticmethod 
    def generate_custom_portfolio_id(user_id: int, portfolio_name: str) -> str:
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', portfolio_name)[:10]
        return f"CUSTOM-{user_id}-{safe_name}-{unique_id}"
    
    @staticmethod
    def parse_portfolio_id(portfolio_id: str) -> Dict[str, Any]:
        parts = portfolio_id.split('_')
        
        if parts[0] == 'GENERAL':
            return {
                'type': 'GENERAL',
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