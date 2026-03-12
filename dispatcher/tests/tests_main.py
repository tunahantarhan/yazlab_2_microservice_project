from fastapi.testclient import TestClient
from dispatcher.main import app 

client = TestClient(app)

def test_read_main():
    # henüz root rotasını yazmadığımız için bu istek 404 dönecek veya import hatası verecek (RED)
    response = client.get("/") # root rotası
    assert response.status_code == 200
    assert response.json() == {"message": "Dispatcher çalışıyor."}