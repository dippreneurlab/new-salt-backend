from pydantic import BaseModel
from typing import Optional


class AuthenticatedUser(BaseModel):
    uid: str
    email: Optional[str] = None
    role: Optional[str] = None
