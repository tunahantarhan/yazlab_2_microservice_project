from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
async def login(data: LoginRequest):
    if data.username == "admin" and data.password == "1234":
        return {
            "access_token": "valid-token",
            "token_type": "bearer",
            "role": "admin"
        }

    raise HTTPException(status_code=401, detail="Geçersiz kullanıcı adı veya şifre.")

class VerifyRequest(BaseModel):
    token: str


@app.post("/auth/verify")
async def verify(data: VerifyRequest):
    if data.token == "valid-token":
        return {
            "valid": True,
            "role": "admin"
        }

    raise HTTPException(status_code=401, detail="Geçersiz token.")
