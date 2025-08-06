from typing import Dict, Any, Optional, Union
from backend.modules.portfolio.repositories import AccountsRepo


class AccountDataProvider:
    repo = AccountsRepo

    @classmethod
    async def get_trading_account(cls, broker_account_id: str) -> Optional[Dict]:
        existing_accounts = await cls.repo.get_by_broker_account_id(
            broker_account_id=broker_account_id
        )

        if not existing_accounts:
            return None

        # Find trading account (type "0449")
        for account in existing_accounts:
            if account.get("accountType") == "0449":
                return account

        return None
