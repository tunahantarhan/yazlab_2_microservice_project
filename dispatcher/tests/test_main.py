import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app
import main as main_module

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Dispatcher çalışıyor."}


class MockResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data


class MockTicketsAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        assert url == "http://ticket_service:8000/tickets"
        return MockResponse([
            {
                "id": 1,
                "event_name": "Konser",
                "price": 250.0,
                "available": True
            }
        ])


def test_dispatcher_forwards_tickets_request(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockTicketsAsyncClient)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "event_name": "Konser",
            "price": 250.0,
            "available": True
        }
    ]


class MockUsersAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        assert url == "http://user_service:8000/users"
        return MockResponse([
            {
                "id": 1,
                "username": "selin",
                "email": "selin@example.com",
                "balance": 500.0
            }
        ])


def test_dispatcher_forwards_users_request(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockUsersAsyncClient)

    response = client.get(
        "/users",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "username": "selin",
            "email": "selin@example.com",
            "balance": 500.0
        }
    ]


class FailingAsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        raise Exception("Service down")


def test_dispatcher_returns_502_when_ticket_service_down(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", FailingAsyncClient)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 502


def test_dispatcher_returns_502_when_user_service_down(monkeypatch):
    monkeypatch.setattr(main_module.httpx, "AsyncClient", FailingAsyncClient)

    response = client.get(
        "/users",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 502


def test_request_without_token_returns_401():
    response = client.get("/tickets")
    assert response.status_code == 401


def test_request_with_invalid_token_returns_403():
    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == 403


def test_dispatcher_forwards_create_ticket_request(monkeypatch):
    class MockPostTicketsAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            assert url == "http://ticket_service:8000/tickets"
            assert json == {
                "id": 1,
                "event_name": "Konser",
                "price": 250.0,
                "available": True
            }
            return MockResponse({
        "message": "Bilet başarıyla eklendi!",
        "id": "mock-ticket-id"},
    status_code=201)

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostTicketsAsyncClient)

    response = client.post(
        "/tickets",
        headers={"Authorization": "Bearer valid-token"},
        json={
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

def test_dispatcher_forwards_create_user_request(monkeypatch):
    class MockPostUsersAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            assert url == "http://user_service:8000/users"
            assert json == {
                "id": 1,
                "username": "selin",
                "email": "selin@example.com",
                "balance": 500.0
            }
            return MockResponse({
        "message": "Kullanıcı başarıyla eklendi!",
        "id": "mock-user-id"},
    status_code=201 )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostUsersAsyncClient)

    response = client.post(
        "/users",
        headers={"Authorization": "Bearer valid-token"},
        json={
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

def test_dispatcher_forwards_update_ticket_request(monkeypatch):
    class MockPatchTicketsAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def patch(self, url, json):
            assert url == "http://ticket_service:8000/tickets/1"
            assert json == {
                "available": False
            }
            return MockResponse(
                {
                    "message": "Bilet müsaitlik durumu başarıyla güncellendi!",
                    "ticket_id": 1,
                    "available": False
                },
                status_code=200
            )

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchTicketsAsyncClient)

    response = client.patch(
        "/tickets/1",
        headers={"Authorization": "Bearer valid-token"},
        json={"available": False}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Bilet müsaitlik durumu başarıyla güncellendi!",
        "ticket_id": 1,
        "available": False
    }

def test_dispatcher_forwards_update_user_request(monkeypatch):
    class MockPatchUsersAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def patch(self, url, json):
            assert url == "http://user_service:8000/users/1"
            assert json == {
                "balance": 1000.0
            }
            return MockResponse(
    {
        "message": "Kullanıcı bakiyesi başarıyla güncellendi!",
        "user_id": 1,
        "new_balance": 1000.0
    },
    status_code=200
)

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchUsersAsyncClient)

    response = client.patch(
        "/users/1",
        headers={"Authorization": "Bearer valid-token"},
        json={"balance": 1000.0}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Kullanıcı bakiyesi başarıyla güncellendi!",
        "user_id": 1,
        "new_balance": 1000.0
    }

def test_dispatcher_forwards_delete_ticket_request(monkeypatch):
    class MockDeleteTicketsAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def delete(self, url):
            assert url == "http://ticket_service:8000/tickets/1"
            return MockResponse(
    {
        "message": "Bilet ID:'1' başarıyla silindi."
    },
    status_code=200
)

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteTicketsAsyncClient)

    response = client.delete(
        "/tickets/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Bilet ID:'1' başarıyla silindi."
    }

def test_dispatcher_forwards_delete_user_request(monkeypatch):
    class MockDeleteUsersAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def delete(self, url):
            assert url == "http://user_service:8000/users/1"
            return MockResponse({
                "message": "Kullanıcı ID:'1' başarıyla silindi."
            })

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteUsersAsyncClient)

    response = client.delete(
        "/users/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Kullanıcı ID:'1' başarıyla silindi."
    }

def test_dispatcher_preserves_ticket_service_404_status(monkeypatch):
    class Mock404Response:
        status_code = 404

        def json(self):
            return {"detail": "Ticket not found"}

    class Mock404AsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            assert url == "http://ticket_service:8000/tickets"
            return Mock404Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", Mock404AsyncClient)

    response = client.get(
        "/tickets",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}

def test_dispatcher_preserves_user_service_404_status(monkeypatch):
    class Mock404Response:
        status_code = 404

        def json(self):
            return {"detail": "User not found"}

    class Mock404AsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def get(self, url):
            assert url == "http://user_service:8000/users"
            return Mock404Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", Mock404AsyncClient)

    response = client.get(
        "/users",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_dispatcher_preserves_ticket_post_400_status(monkeypatch):
    class Mock400Response:
        status_code = 400

        def json(self):
            return {"detail": "Invalid ticket data"}

    class MockPostAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            assert url == "http://ticket_service:8000/tickets"
            return Mock400Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostAsyncClient)

    response = client.post(
        "/tickets",
        headers={"Authorization": "Bearer valid-token"},
        json={"wrong": "data"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid ticket data"}

def test_dispatcher_preserves_user_post_400_status(monkeypatch):
    class Mock400Response:
        status_code = 400

        def json(self):
            return {"detail": "Invalid user data"}

    class MockPostAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def post(self, url, json):
            assert url == "http://user_service:8000/users"
            return Mock400Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPostAsyncClient)

    response = client.post(
        "/users",
        headers={"Authorization": "Bearer valid-token"},
        json={"wrong": "data"}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid user data"}

def test_dispatcher_preserves_ticket_patch_404_status(monkeypatch):
    class Mock404Response:
        status_code = 404

        def json(self):
            return {"detail": "Ticket not found"}

    class MockPatchAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def patch(self, url, json):
            assert url == "http://ticket_service:8000/tickets/1"
            return Mock404Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchAsyncClient)

    response = client.patch(
        "/tickets/1",
        headers={"Authorization": "Bearer valid-token"},
        json={"available": False}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}

def test_dispatcher_preserves_user_patch_404_status(monkeypatch):
    class Mock404Response:
        status_code = 404

        def json(self):
            return {"detail": "User not found"}

    class MockPatchAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def patch(self, url, json):
            assert url == "http://user_service:8000/users/1"
            return Mock404Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockPatchAsyncClient)

    response = client.patch(
        "/users/1",
        headers={"Authorization": "Bearer valid-token"},
        json={"balance": 1000.0}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_dispatcher_preserves_ticket_delete_404_status(monkeypatch):
    class Mock404Response:
        status_code = 404

        def json(self):
            return {"detail": "Ticket not found"}

    class MockDeleteAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def delete(self, url):
            assert url == "http://ticket_service:8000/tickets/1"
            return Mock404Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteAsyncClient)

    response = client.delete(
        "/tickets/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticket not found"}

def test_dispatcher_preserves_user_delete_404_status(monkeypatch):
    class Mock404Response:
        status_code = 404

        def json(self):
            return {"detail": "User not found"}

    class MockDeleteAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def delete(self, url):
            assert url == "http://user_service:8000/users/1"
            return Mock404Response()

    monkeypatch.setattr(main_module.httpx, "AsyncClient", MockDeleteAsyncClient)

    response = client.delete(
        "/users/1",
        headers={"Authorization": "Bearer valid-token"}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
