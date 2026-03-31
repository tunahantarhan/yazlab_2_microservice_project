from pydantic import BaseModel
from typing import Optional

class Ticket(BaseModel):
    id: int
    event_name: str
    price: float
    available: bool

class TicketUpdate(BaseModel):
    event_name: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None