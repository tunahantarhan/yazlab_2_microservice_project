from fastapi.testclient import TestClient
from dispatcher.main import app
import dispatcher.main as main_module

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Dispatcher çalışıyor."}


class MockResponse:
    def __init__(self, data):
        self._data = data

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

    response = client.get("/tickets")

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

    response = client.get("/users")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "username": "selin",
            "email": "selin@example.com",
            "balance": 500.0
        }
    ]
