from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/", "/auth"]:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    if auth_header != "Bearer valid-token":
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    return await call_next(request)


@app.get("/")
async def root():
    return {"message": "Dispatcher çalışıyor."}


@app.get("/tickets")
async def tickets():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ticket_service:8000/tickets")
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Ticket servisine ulaşılamadı.")


@app.post("/tickets")
async def create_ticket(ticket: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://ticket_service:8000/tickets",
                json=ticket
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Ticket servisine ulaşılamadı.")


@app.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: int, data: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"http://ticket_service:8000/tickets/{ticket_id}",
                json=data
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Ticket servisine ulaşılamadı.")


@app.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://ticket_service:8000/tickets/{ticket_id}"
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Ticket servisine ulaşılamadı.")


@app.get("/users")
async def users():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://user_service:8000/users")
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="User servisine ulaşılamadı.")


@app.post("/users")
async def create_user(user: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://user_service:8000/users",
                json=user
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="User servisine ulaşılamadı.")


@app.patch("/users/{user_id}")
async def update_user(user_id: int, data: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"http://user_service:8000/users/{user_id}",
                json=data
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="User servisine ulaşılamadı.")


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://user_service:8000/users/{user_id}"
            )
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
