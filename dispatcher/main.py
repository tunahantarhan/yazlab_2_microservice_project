from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Dispatcher çalışıyor."}


@app.get("/tickets")
async def tickets():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ticket_service:8000/tickets")
            return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Ticket servisine ulaşılamadı.")


@app.get("/users")
async def users():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://user_service:8000/users")
            return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="User servisine ulaşılamadı.")


@app.get("/auth")
async def auth():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://auth_service:8000/auth")
            return response.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Auth servisine ulaşılamadı.")
