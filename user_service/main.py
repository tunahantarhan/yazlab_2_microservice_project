from fastapi import FastAPI, status, HTTPException, Body
from typing import List
from models import User, UserUpdate # pydantic modeli models.py'den import ediliyor
from database import user_collection

app = FastAPI()
users_root = "/users"

# RMM Seviye 2 -> kullanıcı eklemek için "POST" metodu.
@app.post(users_root, status_code=status.HTTP_201_CREATED)
async def create_user(user: User):
    user_dict = user.model_dump()
    result = await user_collection.insert_one(user_dict)
    
    if result.inserted_id:
        return {"message": "Kullanıcı başarıyla eklendi!", "id": str(result.inserted_id)}
    
    raise HTTPException(status_code=500, detail="Kullanıcı veritabanına kaydedilemedi.")

# RMM Seviye 2 -> kullanıcıları listelemek için "GET" metodu.
@app.get(users_root, status_code=status.HTTP_200_OK, response_model=List[User])
async def list_users():
    cursor = user_collection.find({}, {"_id": 0})
    users = await cursor.to_list(length=100)
    
    if not users:
        raise HTTPException(status_code=404, detail="Sistemde henüz kullanıcı bulunmamaktadır.")
        
    return users

# RMM Seviye 2 -> kısmı güncelleme (kullanıcı bakiyesi) işlemleri için "PATCH" metodu.
@app.patch(f"{users_root}/{{user_id}}", status_code=status.HTTP_200_OK)
async def update_user(user_id: int, update_data: UserUpdate):
    # sadece kullanıcı tarafından değiştirilen/girilen kısımlar dict'e çevrilir
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="Güncellenecek veri sağlanmadı.")

    # sadece update dictionary'sinin içindekiler güncellenir
    result = await user_collection.update_one(
        {"id": user_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Güncellenecek kullanıcı bulunamadı.")
        
    return {
        "message": "Kullanıcı başarıyla güncellendi!", 
        "user_id": user_id, 
        "updated_fields": update_dict
    }

# RMM Seviye 2 -> kullanıcı kaydı silme işlemleri için "DELETE" metodu.
@app.delete(f"{users_root}/{{user_id}}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int):
    # id'si eşleşen kullanıcının kaydı silinir.
    result = await user_collection.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Silinecek kullanıcı bulunamadı.")
        
    return {"message": f"Kullanıcı ID:'{user_id}' başarıyla silindi."}

@app.get("/health")
async def health_check():
    return {"status": "User Service sağlıklı durumda."}