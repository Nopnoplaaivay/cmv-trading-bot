from typing import Dict, Optional
from pydantic import BaseModel

class JwtPayload(BaseModel):
    sessionId: str
    userId: int
    role: str
    iat: Optional[int] = None
    exp: Optional[int] = None

class RefreshPayload(JwtPayload):
    signature: str
