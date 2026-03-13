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
    return {"message": "User servisine yönlendirilecek."}


@app.get("/auth")
async def auth():
    return {"message": "Auth servisine yönlendirilecek."}
