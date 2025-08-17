from typing import Optional
from backend.modules.base.dto import BaseDTO


class UpdateRoleDTO(BaseDTO):
    target_account: str
    new_role: str


class CreateUserDTO(BaseDTO):
    account: str
    password: str
    role: str = "free"
    mobile: Optional[str] = None
    email: Optional[str] = None


class UpdateUserInfoDTO(BaseDTO):
    target_account: str
    new_password: Optional[str] = None
    new_role: Optional[str] = None
    new_mobile: Optional[str] = None
    new_email: Optional[str] = None
