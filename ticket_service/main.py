from fastapi import FastAPI, status, HTTPException
from typing import List
from .models import Ticket # pydantic modeli models.py'den import ediliyor
from .database import ticket_collection

app = FastAPI()
tickets_root = "/tickets"

# rmm seviye 2 gereği kayıt eklemek için "post" metodunu kullanıyoruz
@app.post(tickets_root, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket: Ticket):
    # pydantic modeli dictionary olarak alıp mongodb'ye yolluyoruz
    ticket_dict = ticket.model_dump()
    
    result = await ticket_collection.insert_one(ticket_dict)
    
    if result.inserted_id:
        return {"message": "Bilet başarıyla eklendi!", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=500, detail="Bilet veritabanına kaydedilemedi.") 

# rmm seviye 2 gereği kayıt listelemek için "get" metodunu kullanıyoruz.
@app.get(tickets_root, status_code=status.HTTP_200_OK, response_model=List[Ticket])
async def list_tickets():
    cursor = ticket_collection.find({}, {"_id": 0}) # {"_id": 0} ile mongodb'nin otomatik ürettiği "ObjectId" gizlenir,
    tickets = await cursor.to_list(length=100) # böylece pydantic modelimizdeki kendi "id" verdiğimiz alan ile çakışmaz.
    
    if not tickets:
        raise HTTPException(status_code=404, detail="Sistemde henüz bilet bulunmamaktadır.")
        
    return tickets

@app.get("/health")
async def health_check():
    return {"status": "Ticket Service sağlıklı durumda."}