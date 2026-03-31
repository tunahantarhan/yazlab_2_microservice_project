from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
import httpx
from fastapi.security import HTTPBearer
from fastapi import Depends

app = FastAPI()
security = HTTPBearer()

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # token istemeyen rotalar listesi (white list)
    public_paths = [
        "/", 
        "/auth", 
        "/auth/login", 
        "/metrics", 
        "/docs", 
        "/openapi.json", 
        "/redoc"
    ]
    if request.url.path in public_paths:
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    token = auth_header.replace("Bearer ", "")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://auth_service:8000/auth/verify",
                json={"token": token}
            )

            if response.status_code != 200:
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})

            data = response.json()

            if not data.get("valid"):
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    except Exception:
        return JSONResponse(
            status_code=502,
            content={"detail": "Auth servisine ulaşılamadı."}
        )

    return await call_next(request)


@app.get("/")
async def root():
    return {"message": "Dispatcher çalışıyor."}


@app.get("/tickets", dependencies=[Depends(security)])
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


@app.post("/tickets", dependencies=[Depends(security)])
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


@app.delete("/tickets/{ticket_id}", dependencies=[Depends(security)])
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


@app.get("/users", dependencies=[Depends(security)])
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


@app.post("/users", dependencies=[Depends(security)])
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


@app.patch("/users/{user_id}", dependencies=[Depends(security)])
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


@app.delete("/users/{user_id}", dependencies=[Depends(security)])
async def delete_user(user_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://user_service:8000/users/{user_id}"
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="User servisine ulaşılamadı.")


@app.get("/auth")
async def auth():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://auth_service:8000/auth")
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Auth servisine ulaşılamadı.")
    
@app.post("/auth/login")
async def login(credentials: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            # gelen kullanıcı bilgileri iç ağdaki auth servisine yönlendirilir
            response = await client.post(
                "http://auth_service:8000/auth/login",
                json=credentials
            )
            return JSONResponse(
                status_code=response.status_code,
                content=response.json()
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Auth servisine ulaşılamadı.")


Instrumentator().instrument(app).expose(app)
