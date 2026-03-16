from fastapi import FastAPI, status, HTTPException
from typing import List
from .models import User # pydantic modeli models.py'den import ediliyor
from .database import user_collection

app = FastAPI()
users_root = "/users"

# rmm seviye 2 gereği kullanıcı eklemek için "post" metodunu kullanıyoruz
@app.post(users_root, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    user_dict = user.model_dump()
    result = await user_collection.insert_one(user_dict)
    
    if result.inserted_id:
        return {"message": "Kullanıcı başarıyla eklendi!", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=500, detail="Kullanıcı veritabanına kaydedilemedi.")

@app.get("/health")
async def health_check():
    return {"status": "User Service sağlıklı durumda."}