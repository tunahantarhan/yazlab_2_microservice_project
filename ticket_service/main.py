from fastapi import FastAPI, status, HTTPException
from typing import List
from .models import Ticket # pydantic modeli models.py'den import ediliyor
from .database import ticket_collection

app = FastAPI()
tickets_root = "/tickets"

# rmm seviye 2 gereği kayıt eklemek için "post" kullanıyoruz
@app.post(tickets_root, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket: Ticket):
    # pydantic modeli dictionary olarak alıp mongodb'ye yolluyoruz
    ticket_dict = ticket.model_dump()
    
    result = await ticket_collection.insert_one(ticket_dict)
    
    if result.inserted_id:
        return {"message": "Bilet başarıyla eklendi!", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=500, detail="Bilet veritabanına kaydedilemedi.") 

@app.get("/health")
async def health_check():
    return {"status": "Ticket Service sağlıklı durumda."}