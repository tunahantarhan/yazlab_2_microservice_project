from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from database import users_collection
from security import verify_password, create_access_token, verify_token
from init_db import create_initial_admin
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # başlangıçta ilk olarak init_db'deki db kontrol fonksiyonu çalışır
    await create_initial_admin()
    yield
    
app = FastAPI(lifespan=lifespan)

class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
async def login(data: LoginRequest):
    # kullanıcı mongodb'den bulunur
    user = await users_collection.find_one({"username": data.username})
    
    # kullanıcı bulunamazsa ya da şifresi uyuşmazsa 401 kodu geri döndürülür
    if not user or not verify_password(data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz kullanıcı adı veya şifre."
        )

    # her şey uygun ise gerçek json web token oluşturulur
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"]
    }