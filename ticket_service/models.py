from pydantic import BaseModel

class Ticket(BaseModel):
    id: int
    event_name: str
    price: float
    available: bool