from fastapi import FastAPI, status, HTTPException
from typing import List
from .models import Ticket # pydantic modeli models.py'den import ediliyor

app = FastAPI()
tickets_root = "/tickets"

# nosql database bağlanana kadar mock veriler
fake_tickets_db = [
    {"id": 1, "event_name": "Yazlab Konseri", "price": 150.0, "available": True},
    {"id": 2, "event_name": "Mikroservis Filmi", "price": 0.0, "available": True}
]

# rmm 2 gereği "get" ile root'a erişiyoruz
@app.get(tickets_root, status_code=status.HTTP_200_OK, response_model=List[Ticket])
async def list_tickets():
    if not fake_tickets_db:
        raise HTTPException(status_code=404, detail="Bilet bulunamadı.")
    return fake_tickets_db # mock db

@app.get("/health")
async def health_check():
    return {"status": "Ticket Service sağlıklı durumda."}