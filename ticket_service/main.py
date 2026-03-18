from fastapi import FastAPI, status, HTTPException, Body
from typing import List, Optional
from .models import Ticket # pydantic modeli models.py'den import ediliyor
from .database import ticket_collection

app = FastAPI()
tickets_root = "/tickets"

# RMM Seviye 2 -> bilet eklemek için "POST" metodu.
@app.post(tickets_root, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket: Ticket):
    # pydantic modeli dictionary olarak alıp mongodb'ye yolluyoruz
    ticket_dict = ticket.model_dump()
    
    result = await ticket_collection.insert_one(ticket_dict)
    
    if result.inserted_id:
        return {"message": "Bilet başarıyla eklendi!", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=500, detail="Bilet veritabanına kaydedilemedi.") 

# RMM Seviye 2 -> biletleri listelemek için "GET" metodu.
@app.get(tickets_root, status_code=status.HTTP_200_OK, response_model=List[Ticket])
async def list_tickets(available: Optional[bool] = None):
    # eğer biletler availability'sine göre filtrelenmek istenirse:
    query = {}
    if available is not None:
        query["available"] = available
        
    cursor = ticket_collection.find(query, {"_id": 0}) # {"_id": 0} ile mongodb'nin otomatik ürettiği "ObjectId" gizlenir,
    tickets = await cursor.to_list(length=100) # böylece pydantic modelimizdeki kendi "id" verdiğimiz alan ile çakışmaz.
    
    if not tickets:
        raise HTTPException(status_code=404, detail="Sistemde henüz bilet bulunmamaktadır.")
        
    return tickets

# RMM Seviye 2 -> kısmi güncelleme (bilet availability) işlemleri için "PATCH" metodu.
@app.patch(f"{tickets_root}/{{ticket_id}}", status_code=status.HTTP_200_OK)
async def update_ticket_status(ticket_id: int, available: bool = Body(..., embed=True)):
    # id'si eşleşen ticket'ın sadece "available" kısmı güncellenir.
    result = await ticket_collection.update_one(
        {"id": ticket_id},
        {"$set": {"available": available}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Güncellenecek bilet bulunamadı.")
        
    return {
        "message": "Bilet müsaitlik durumu başarıyla güncellendi!", 
        "ticket_id": ticket_id, 
        "available": available
    }
    
# RMM Seviye 2 -> bilet kaydı silme işlemleri için "DELETE" metodu.
@app.delete(f"{tickets_root}/{{ticket_id}}", status_code=status.HTTP_200_OK)
async def delete_ticket(ticket_id: int):
    # id'si eşleşen biletin kaydı silinir.
    result = await ticket_collection.delete_one({"id": ticket_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Silinecek bilet bulunamadı.")
        
    return {"message": f"Bilet ID:'{ticket_id}' başarıyla silindi."}

@app.get("/health")
async def health_check():
    return {"status": "Ticket Service sağlıklı durumda."}