from typing import Optional
from backend.modules.base.dto import BaseDTO


class SetupDNSEAccountDTO(BaseDTO):
    username: str
    password: str


# class AccountBalanceResponseDTO(BaseDTO):
#     account_id: str
#     broker_account_id: str
#     total_cash: Optional[int] = None
#     available_cash: Optional[int] = None
#     stock_value: Optional[int] = None
#     net_asset_value: Optional[int] = None
#     purchasing_power: Optional[int] = None
#     margin_debt: Optional[float] = None
#     margin_rate: Optional[float] = None


# class AccountSetupResponseDTO(BaseDTO):
#     message: str
#     broker_account_id: str
#     balance_updated: bool
#     balance_info: Optional[AccountBalanceResponseDTO] = None
