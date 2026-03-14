from fastapi import FastAPI, status, HTTPException
from typing import Optional
from .models import User # pydantic modeli models.py'den import ediliyor

app = FastAPI()
users_root = "/profile"

# mongodb ile gerçek db bağlanana kadar mock veriler
fake_user_db = {
    "ogrenci1": {"username": "ogrenci1", "email": "ogrenci@universite.edu.tr", "full_name": "Deneme Kullanıcısı", "is_active": True}
}

# rmm 2 doğrultusunda "get" ile root'a erişim
@app.get(f"users_root/{{username}}", status_code=status.HTTP_200_OK, response_model=UserProfile)
async def get_profile(username: str):
    user = fake_user_db.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    return user

@app.get("/health")
async def health_check():
    return {"status": "User Service sağlıklı durumda."}