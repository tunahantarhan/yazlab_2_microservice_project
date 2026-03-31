from pydantic import BaseModel
from typing import Optional

class LoginModel(BaseModel):
    username: str
    password: str

class TicketModel(BaseModel):
    id: int
    event_name: str
    price: float
    available: bool

class TicketUpdateModel(BaseModel):
    event_name: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None

class UserModel(BaseModel):
    id: int
    username: str
    email: str
    balance: float

class UserUpdateModel(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    balance: Optional[float] = None