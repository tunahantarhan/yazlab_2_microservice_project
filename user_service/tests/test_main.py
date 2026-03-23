import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app) # fastapi test client'ı

# main.py'deki health check rotasına ulaşım.
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "User Service sağlıklı durumda."}
    
# mock veritabanı ve veriler
mock_user_data = [
    {"id": 1, "username": "tunahan", "email": "tunahan@example.com", "balance": 5000.0},
    {"id": 2, "username": "sukran", "email": "sukran@example.com", "balance": 150.0}
]

# "patch" ile user listelemeyi taklit ediyoruz
@patch("main.user_collection.find")
def test_list_all_users(mock_find):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = mock_user_data
    mock_find.return_value = mock_cursor

    # test isteği
    response = client.get("/users")

    assert response.status_code == 200
    assert len(response.json()) == 2
    
    assert response.json()[0]["username"] == "tunahan"
    assert response.json()[0]["balance"] == 5000.0
    
    mock_find.assert_called_with({}, {"_id": 0})
    
# "patch" ile user eklemeyi taklit ediyoruz
@patch("main.user_collection.insert_one", new_callable=AsyncMock)
def test_create_user(mock_insert):
    class MockInsertResult:
        inserted_id = "mocked-mongo-user-id"

    mock_insert.return_value = MockInsertResult()

    # gönderilecek mock user
    new_user_data = {
        "id": 3,
        "username": "yeni_transfer",
        "email": "transfer@example.com",
        "balance": 1500.0
    }

    response = client.post("/users", json=new_user_data)

    assert response.status_code == 201
    assert response.json()["message"] == "Kullanıcı başarıyla eklendi!"
    
    # fonksiyon mongodb'ye göndermeye çalışmış mı?
    mock_insert.assert_called_once_with(new_user_data)

# "patch" ile asenkron olarak user güncellemeyi taklit ediyoruz
@patch("main.user_collection.update_one", new_callable=AsyncMock)
def test_update_user_balance(mock_update):
    class MockUpdateResult:
        matched_count = 1 # "1 user bulundu -> güncellendi"

    mock_update.return_value = MockUpdateResult()

    # bilet satışı sonrası bakiye düşme senaryosu simülasyonu
    response = client.patch("/users/1", json={"balance": 3000.0})

    assert response.status_code == 200
    assert response.json()["message"] == "Kullanıcı bakiyesi başarıyla güncellendi!" 

    # "fonksiyon veritabanıyla doğru etkileşime girmiş mi?"
    mock_update.assert_called_once_with(
        {"id": 1},
        {"$set": {"balance": 3000.0}}
    )
    
# user silme senaryosu (başarılı senaryo)
@patch("main.user_collection.delete_one", new_callable=AsyncMock)
def test_delete_user_success(mock_delete):
    class MockDeleteResult:
        deleted_count = 1

    mock_delete.return_value = MockDeleteResult()

    response = client.delete("/users/1")

    assert response.status_code == 200
    assert response.json()["message"] == "Kullanıcı ID:'1' başarıyla silindi."
    mock_delete.assert_called_once_with({"id": 1})

# olmayan user'ı silme senaryosu (başarısız senaryo)
@patch("main.user_collection.delete_one", new_callable=AsyncMock)
def test_delete_user_not_found(mock_delete):
    class MockDeleteResult:
        deleted_count = 0

    mock_delete.return_value = MockDeleteResult()

    response = client.delete("/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Silinecek kullanıcı bulunamadı."