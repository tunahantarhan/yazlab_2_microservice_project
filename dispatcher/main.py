from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Dispatcher çalışıyor."}

@app.get("/tickets")
async def tickets():
    return {"message": "Ticket servisine yönlendirilecek."}
    
@app.get("/users")
async def users():
    return {"message": "User servisine yönlendirilecek."}
