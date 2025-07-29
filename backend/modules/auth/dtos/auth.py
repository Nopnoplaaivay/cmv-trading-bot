from typing import Optional
from backend.modules.base.dto import BaseDTO

class RegisterDTO(BaseDTO):
    account: str
    password: str
    confirm_password: str
    role: str

class LoginDTO(BaseDTO):
    account: str
    password: str

class LogoutDTO(BaseDTO):
    sessionId: str
    userId: int
    role: str
    iat: Optional[int] = None
    exp: Optional[int] = None

class RefreshDTO(LogoutDTO):
    signature: str

class LoginResDTO(BaseDTO):
    access_token: str
    refresh_token: str

class RefreshResDTO(BaseDTO):
    access_token: str