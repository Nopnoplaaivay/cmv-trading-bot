from typing import Optional
from backend.modules.base.dto import BaseDTO


class SetupDNSEAccountDTO(BaseDTO):
    username: str
    password: str


class DefaultAccountResponseDTO(BaseDTO):
    account_id: str
    name: str
    custody_code: str
    broker_account_id: str
    broker_name: str = "DNSE"
    broker_investor_id: str
    is_default: bool = True