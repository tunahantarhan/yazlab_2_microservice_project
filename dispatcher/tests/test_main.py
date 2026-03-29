import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
import main as main_module

client = TestClient(app)


# =========================
# ORTAK MOCK YAPILARI
# =========================

class MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class BaseAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, url, json):
        # Auth middleware artık önce burayı çağırıyor
        if url == "http://auth_service:8000/auth/verify":
            token = json.get("token")

            if token == "valid-token":
                return MockResponse(
                    {"valid": True, "role": "admin"},
                    status_code=200
                )

            return MockResponse(
                {"detail": "Geçersiz token."},
                status_code=401
            )

        raise NotImplementedError(f"POST için mock tanımlanmadı: {url}")


class FailingAsyncClient(BaseAsyncClient):
    async def get(self, url):
        raise Exception("Service down")

    async def patch(self, url, json):
        raise Exception("Service down")

    async def delete(self, url):
        raise Exception("Service down")


# =========================
# HELPER FONKSİYONLAR
# =========================

VALID_HEADERS = {"Authorization": "Bearer valid-token"}


def auth_get(path: str):
    return client.get(path, headers=VALID_HEADERS)


def auth_post(path: str, payload: dict):
    return client.post(path, headers=VALID_HEADERS, json=payload)


def auth_patch(path: str, payload: dict):
    return client.patch(path, headers=VALID_HEADERS, json=payload)


def auth_delete(path: str):
    return client.delete(path, headers=VALID_HEADERS)


# =========================
# TEMEL TESTLER
# =========================

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Dispatcher çalışıyor."}


def test_request_without_token_returns_401():
    response = client.get("/tickets")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_request_with_invalid_token_returns_403(monkeypatch):
    class MockInvalidAuthClient(BaseAsyncClient):
        async def post(self, url, json):
            assert url == "http://auth_service:8000/auth/verify"
            assert json == {"token": "invalid"}
            return MockResponse(
                {"detail": "Geçersiz token."},
                status_code=401
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockInvalidAuthClient)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer invalid"}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_request_with_valid_token_calls_auth_service(monkeypatch):
    class MockAuthClient(BaseAsyncClient):
        async def get(self, url):
            assert url == "http://ticket_service:8000/tickets"
            return MockResponse([], status_code=200)

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockAuthClient)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200


# =========================
# GET /tickets
# =========================

def test_dispatcher_forwards_tickets_request(monkeypatch):
    class MockTicketsAsyncClient(BaseAsyncClient):
        async def get(self, url):
            assert url == "http://ticket_service:8000/tickets"
            return MockResponse(
                [
                    {
                        "id": 1,
                        "event_name": "Konser",
                        "price": 250.0,
                        "available": True
                    }
                ],
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockTicketsAsyncClient)

    response = auth_get("/tickets")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "event_name": "Konser",
            "price": 250.0,
            "available": True
        }
    ]


def test_dispatcher_preserves_ticket_service_404_status(monkeypatch):
    class Mock404AsyncClient(BaseAsyncClient):
        async def get(self, url):
            assert url == "http://ticket_service:8000/tickets"
            return MockResponse(
                {"detail": "Ticket not found"},
                status_code=404
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", Mock404AsyncClient)

    response = auth_get("/tickets")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}


def test_dispatcher_returns_502_when_ticket_service_down(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", FailingAsyncClient)

    response = auth_get("/tickets")

    assert response.status_code == 502
    assert response.json() == {"detail": "Ticket servisine ulaşılamadı."}


# =========================
# POST /tickets
# =========================

def test_dispatcher_forwards_create_ticket_request(monkeypatch):
    class MockPostTicketsAsyncClient(BaseAsyncClient):
        async def post(self, url, json):
            if url == "http://auth_service:8000/auth/verify":
                return MockResponse(
                    {"valid": True, "role": "admin"},
                    status_code=200
                )

            assert url == "http://ticket_service:8000/tickets"
            assert json == {
                "id": 1,
                "event_name": "Konser",
                "price": 250.0,
                "available": True
            }
            return MockResponse(
                {
                    "message": "Bilet başarıyla eklendi!",
                    "id": "mock-ticket-id"
                },
                status_code=201
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostTicketsAsyncClient)

    response = auth_post(
        "/tickets",
        {
            "id": 1,
            "event_name": "Konser",
            "price": 250.0,
            "available": True
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Bilet başarıyla eklendi!",
        "id": "mock-ticket-id"
    }


def test_dispatcher_preserves_ticket_post_400_status(monkeypatch):
    class MockPostAsyncClient(BaseAsyncClient):
        async def post(self, url, json):
            if url == "http://auth_service:8000/auth/verify":
                return MockResponse(
                    {"valid": True, "role": "admin"},
                    status_code=200
                )

            assert url == "http://ticket_service:8000/tickets"
            return MockResponse(
                {"detail": "Invalid ticket data"},
                status_code=400
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostAsyncClient)

    response = auth_post("/tickets", {"wrong": "data"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid ticket data"}


# =========================
# PATCH /tickets
# =========================

def test_dispatcher_forwards_update_ticket_request(monkeypatch):
    class MockPatchTicketsAsyncClient(BaseAsyncClient):
        async def patch(self, url, json):
            assert url == "http://ticket_service:8000/tickets/1"
            assert json == {"available": False}
            return MockResponse(
                {
                    "message": "Bilet müsaitlik durumu başarıyla güncellendi!",
                    "ticket_id": 1,
                    "available": False
                },
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchTicketsAsyncClient)

    response = auth_patch("/tickets/1", {"available": False})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Bilet müsaitlik durumu başarıyla güncellendi!",
        "ticket_id": 1,
        "available": False
    }


def test_dispatcher_preserves_ticket_patch_404_status(monkeypatch):
    class MockPatchAsyncClient(BaseAsyncClient):
        async def patch(self, url, json):
            assert url == "http://ticket_service:8000/tickets/1"
            return MockResponse(
                {"detail": "Ticket not found"},
                status_code=404
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchAsyncClient)

    response = auth_patch("/tickets/1", {"available": False})

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}


# =========================
# DELETE /tickets
# =========================

def test_dispatcher_forwards_delete_ticket_request(monkeypatch):
    class MockDeleteTicketsAsyncClient(BaseAsyncClient):
        async def delete(self, url):
            assert url == "http://ticket_service:8000/tickets/1"
            return MockResponse(
                {"message": "Bilet ID:'1' başarıyla silindi."},
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteTicketsAsyncClient)

    response = auth_delete("/tickets/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Bilet ID:'1' başarıyla silindi."
    }


def test_dispatcher_preserves_ticket_delete_404_status(monkeypatch):
    class MockDeleteAsyncClient(BaseAsyncClient):
        async def delete(self, url):
            assert url == "http://ticket_service:8000/tickets/1"
            return MockResponse(
                {"detail": "Ticket not found"},
                status_code=404
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteAsyncClient)

    response = auth_delete("/tickets/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}


# =========================
# GET /users
# =========================

def test_dispatcher_forwards_users_request(monkeypatch):
    class MockUsersAsyncClient(BaseAsyncClient):
        async def get(self, url):
            assert url == "http://user_service:8000/users"
            return MockResponse(
                [
                    {
                        "id": 1,
                        "username": "selin",
                        "email": "selin@example.com",
                        "balance": 500.0
                    }
                ],
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockUsersAsyncClient)

    response = auth_get("/users")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "username": "selin",
            "email": "selin@example.com",
            "balance": 500.0
        }
    ]


def test_dispatcher_preserves_user_service_404_status(monkeypatch):
    class Mock404AsyncClient(BaseAsyncClient):
        async def get(self, url):
            assert url == "http://user_service:8000/users"
            return MockResponse(
                {"detail": "User not found"},
                status_code=404
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", Mock404AsyncClient)

    response = auth_get("/users")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_dispatcher_returns_502_when_user_service_down(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", FailingAsyncClient)

    response = auth_get("/users")

    assert response.status_code == 502
    assert response.json() == {"detail": "User servisine ulaşılamadı."}


# =========================
# POST /users
# =========================

def test_dispatcher_forwards_create_user_request(monkeypatch):
    class MockPostUsersAsyncClient(BaseAsyncClient):
        async def post(self, url, json):
            if url == "http://auth_service:8000/auth/verify":
                return MockResponse(
                    {"valid": True, "role": "admin"},
                    status_code=200
                )

            assert url == "http://user_service:8000/users"
            assert json == {
                "id": 1,
                "username": "selin",
                "email": "selin@example.com",
                "balance": 500.0
            }
            return MockResponse(
                {
                    "message": "Kullanıcı başarıyla eklendi!",
                    "id": "mock-user-id"
                },
                status_code=201
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostUsersAsyncClient)

    response = auth_post(
        "/users",
        {
            "id": 1,
            "username": "selin",
            "email": "selin@example.com",
            "balance": 500.0
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "message": "Kullanıcı başarıyla eklendi!",
        "id": "mock-user-id"
    }


def test_dispatcher_preserves_user_post_400_status(monkeypatch):
    class MockPostAsyncClient(BaseAsyncClient):
        async def post(self, url, json):
            if url == "http://auth_service:8000/auth/verify":
                return MockResponse(
                    {"valid": True, "role": "admin"},
                    status_code=200
                )

            assert url == "http://user_service:8000/users"
            return MockResponse(
                {"detail": "Invalid user data"},
                status_code=400
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostAsyncClient)

    response = auth_post("/users", {"wrong": "data"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid user data"}


# =========================
# PATCH /users
# =========================

def test_dispatcher_forwards_update_user_request(monkeypatch):
    class MockPatchUsersAsyncClient(BaseAsyncClient):
        async def patch(self, url, json):
            assert url == "http://user_service:8000/users/1"
            assert json == {"balance": 1000.0}
            return MockResponse(
                {
                    "message": "Kullanıcı bakiyesi başarıyla güncellendi!",
                    "user_id": 1,
                    "new_balance": 1000.0
                },
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchUsersAsyncClient)

    response = auth_patch("/users/1", {"balance": 1000.0})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Kullanıcı bakiyesi başarıyla güncellendi!",
        "user_id": 1,
        "new_balance": 1000.0
    }


def test_dispatcher_preserves_user_patch_404_status(monkeypatch):
    class MockPatchAsyncClient(BaseAsyncClient):
        async def patch(self, url, json):
            assert url == "http://user_service:8000/users/1"
            return MockResponse(
                {"detail": "User not found"},
                status_code=404
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchAsyncClient)

    response = auth_patch("/users/1", {"balance": 1000.0})

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


# =========================
# DELETE /users
# =========================

def test_dispatcher_forwards_delete_user_request(monkeypatch):
    class MockDeleteUsersAsyncClient(BaseAsyncClient):
        async def delete(self, url):
            assert url == "http://user_service:8000/users/1"
            return MockResponse(
                {"message": "Kullanıcı ID:'1' başarıyla silindi."},
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteUsersAsyncClient)

    response = auth_delete("/users/1")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Kullanıcı ID:'1' başarıyla silindi."
    }


def test_dispatcher_preserves_user_delete_404_status(monkeypatch):
    class MockDeleteAsyncClient(BaseAsyncClient):
        async def delete(self, url):
            assert url == "http://user_service:8000/users/1"
            return MockResponse(
                {"detail": "User not found"},
                status_code=404
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteAsyncClient)

    response = auth_delete("/users/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
