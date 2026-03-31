from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    email: str
    balance: float
    
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    balance: Optional[float] = None