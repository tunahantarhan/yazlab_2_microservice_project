import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app) # fastapi test client'ı.

# main.py'deki health check rotasına ulaşım
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Ticket Service sağlıklı durumda."}
    
# mock veritabanı ve veriler
mock_db_data = [
    {"id": 1, "event_name": "Fenerbahçe - Galatasaray Derbisi", "price": 2000.0, "available": True},
    {"id": 2, "event_name": "Şampiyonlar Ligi Finali", "price": 5000.0, "available": False}
]

# "patch" ile main'deki ticket_collection.find'ı taklit ediyoruz
@patch("main.ticket_collection.find")
def test_list_all_tickets(mock_find):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = mock_db_data
    mock_find.return_value = mock_cursor

    # test isteği
    response = client.get("/tickets")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["event_name"] == "Fenerbahçe - Galatasaray Derbisi"

@patch("main.ticket_collection.find")
def test_list_available_tickets(mock_find):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [mock_db_data[0]]
    mock_find.return_value = mock_cursor

    # filtreli test isteği
    response = client.get("/tickets?available=true")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["available"] is True
    
    mock_find.assert_called_with({"available": True}, {"_id": 0})
    
# "patch" ile bilet eklemeyi taklit ediyoruz
@patch("main.ticket_collection.insert_one", new_callable=AsyncMock)
def test_create_ticket(mock_insert):
    class MockInsertResult:
        inserted_id = "mocked-mongo-id-999"

    mock_insert.return_value = MockInsertResult()

    # gönderilecek mock bilet
    new_ticket_data = {
        "id": 3,
        "event_name": "Teoman Konseri",
        "price": 500.0,
        "available": True
    }

    response = client.post("/tickets", json=new_ticket_data)

    assert response.status_code == 201
    
    assert response.json()["message"] == "Bilet başarıyla eklendi!"
    assert response.json()["id"] == "mocked-mongo-id-999"

    # fonksiyon mongodb'ye göndermeye çalışmış mı?
    mock_insert.assert_called_once_with(new_ticket_data)