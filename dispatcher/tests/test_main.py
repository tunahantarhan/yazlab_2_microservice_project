from fastapi.testclient import TestClient
from dispatcher.main import app 

client = TestClient(app)

def test_read_main():
    # henüz root rotasını yazmadığımız için bu istek 404 dönecek veya import hatası verecek (RED)
    response = client.get("/") # root rotası
    assert response.status_code == 200
    assert response.json() == {"message": "Dispatcher çalışıyor."}

def test_tickets_route_exists():
    response = client.get("/tickets")
    assert response.status_code == 200
    
def test_users_route_exists():
    response = client.get("/users")
    assert response.status_code == 200

def test_auth_route_exists():
    response = client.get("/auth")
    assert response.status_code == 200
