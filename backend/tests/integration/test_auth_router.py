"""Integration tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAuthRouter:
    """Test registration, login, and current user endpoints."""

    def test_register_login_and_me(self, client: TestClient):
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "learner",
                "password": "strong-password",
                "email": "learner@example.com",
            },
        )

        assert register_response.status_code == 200
        register_data = register_response.json()["data"]
        assert register_data["token_type"] == "bearer"
        assert register_data["access_token"]
        assert register_data["user"]["username"] == "learner"

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "learner",
                "password": "strong-password",
            },
        )

        assert login_response.status_code == 200
        token = login_response.json()["data"]["access_token"]

        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert me_response.status_code == 200
        assert me_response.json()["data"]["username"] == "learner"

    def test_register_rejects_short_password(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "learner",
                "password": "short",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"]["error"]["code"] == "AUTH_REGISTER_FAILED"

    def test_login_rejects_bad_password(self, client: TestClient):
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "learner",
                "password": "strong-password",
            },
        )

        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "learner",
                "password": "wrong-password",
            },
        )

        assert response.status_code == 401
        assert response.json()["detail"]["error"]["code"] == "AUTH_LOGIN_FAILED"

    def test_me_requires_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
