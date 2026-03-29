from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_login_returns_token_for_valid_credentials():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "1234"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "valid-token",
        "token_type": "bearer",
        "role": "admin"
    }

def test_login_returns_401_for_invalid_credentials():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin",
            "password": "wrong"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Geçersiz kullanıcı adı veya şifre."
    }

def test_verify_returns_valid_true_for_valid_token():
    response = client.post(
        "/auth/verify",
        json={
            "token": "valid-token"
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "role": "admin"
    }


def test_verify_returns_401_for_invalid_token():
    response = client.post(
        "/auth/verify",
        json={
            "token": "wrong-token"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Geçersiz token."
    }
