from fastapi.testclient import TestClient
from main import app
import pytest
from security import get_password_hash, create_access_token

# mock veritabanı oluşturma
class MockUsersCollection:
    async def find_one(self, query):
        if query.get("username") == "admin":
            return {
                "username": "admin",
                "hashed_password": "fake-hashed-password",
                "role": "admin"
            }
        return None

# testler öncesi mock veritabanının sisteme aktarılması
@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    monkeypatch.setattr("main.users_collection", MockUsersCollection())
    
    # testlerde init_db'deki veritabanı kontrolü atlanıyor
    async def mock_init():
        pass
    monkeypatch.setattr("main.create_initial_admin", mock_init)
    
    # güncel bcrypt "72 karakterden uzun şifre olamaz" bug'ı dolayısıyla mock şifre ve hash'lenmiş şifre kullanıyoruz
    def mock_verify_password(plain_password, hashed_password):
        return plain_password == "1234" and hashed_password == "fake-hashed-password"
    monkeypatch.setattr("main.verify_password", mock_verify_password)

# ---- TESTLER ----

# client = TestClient(app) -> geçersiz kılıyoruz
# başlangıçta lifespan/startup eventleri olduğu için her testin içinde bunu "with TestClient(app) as client" şeklinde belirtiyoruz

def test_login_returns_token_for_valid_credentials():
    with TestClient(app) as client:
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "1234"}
        )
    
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["role"] == "admin"

def test_login_returns_401_for_invalid_credentials():
    with TestClient(app) as client:
        response = client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong"}
        )
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Geçersiz kullanıcı adı veya şifre."}

def test_verify_returns_valid_true_for_valid_token():
    # test için gerçek geçerli bir token üretiliyor
    valid_token = create_access_token(data={"sub": "admin", "role": "admin"})
    
    with TestClient(app) as client:
        response = client.post(
            "/auth/verify",
            json={"token": valid_token}
        )
        
        assert response.status_code == 200
        assert response.json() == {
            "valid": True,
            "role": "admin"
        }

def test_verify_returns_401_for_invalid_token():
    with TestClient(app) as client:
        response = client.post(
            "/auth/verify",
            json={"token": "wrong-token"}
        )
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Geçersiz veya süresi dolmuş token."}
