"""
Integration tests for settings API endpoints.

Tests:
- GET /api/v1/settings - Settings retrieval
- PUT /api/v1/settings - Settings update
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_data.fixtures import sample_settings


@pytest.mark.integration
class TestSettingsRouter:
    """Test suite for settings API endpoints."""

    # GET /api/v1/settings tests

    def test_get_settings_success(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/settings returns successful response."""
        # Act
        response = client.get("/api/v1/settings")

        # Assert
        assert response.status_code == 200

    def test_get_settings_response_structure(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/settings returns correct response structure."""
        # Act
        response = client.get("/api/v1/settings")

        # Assert
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert isinstance(data["request_id"], str)
        assert isinstance(data["data"], dict)

    def test_get_settings_includes_request_id(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/settings includes valid request_id."""
        # Act
        response = client.get("/api/v1/settings")

        # Assert
        data = response.json()
        request_id = data["request_id"]
        assert len(request_id) > 0
        # Request ID should be a UUID
        assert "-" in request_id

    def test_get_settings_empty_database(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/settings returns empty dict when no settings exist."""
        # Act
        response = client.get("/api/v1/settings")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data == {}

    def test_get_settings_with_data(self, client: TestClient, test_db: Session):
        """Test GET /api/v1/settings returns configured settings."""
        # Arrange
        from app.models import Setting

        setting1 = Setting(key="daily_new_limit", value=25)
        setting2 = Setting(key="daily_review_limit", value=150)
        setting3 = Setting(key="default_source_scope", value=[1, 2])
        test_db.add_all([setting1, setting2, setting3])
        test_db.commit()

        # Act
        response = client.get("/api/v1/settings")

        # Assert
        data = response.json()["data"]
        assert data["daily_new_limit"] == 25
        assert data["daily_review_limit"] == 150
        assert data["default_source_scope"] == [1, 2]

    def test_get_settings_with_fixture(self, client: TestClient, test_db: Session, sample_settings):
        """Test GET /api/v1/settings works with sample_settings fixture."""
        # Act
        response = client.get("/api/v1/settings")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) >= 4

    # PUT /api/v1/settings tests

    def test_update_settings_success(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings returns successful response."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": 30}
        )

        # Assert
        assert response.status_code == 200

    def test_update_settings_response_structure(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings returns correct response structure."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": 30}
        )

        # Assert
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert isinstance(data["request_id"], str)
        assert isinstance(data["data"], dict)

    def test_update_settings_single_field(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings can update single field."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": 30}
        )

        # Assert
        data = response.json()["data"]
        assert data["daily_new_limit"] == 30

    def test_update_settings_multiple_fields(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings can update multiple fields."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={
                "daily_new_limit": 25,
                "daily_review_limit": 150
            }
        )

        # Assert
        data = response.json()["data"]
        assert data["daily_new_limit"] == 25
        assert data["daily_review_limit"] == 150

    def test_update_settings_returns_all_settings(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings returns all settings, not just updated ones."""
        # Arrange - create initial settings
        from app.models import Setting

        setting1 = Setting(key="daily_new_limit", value=20)
        setting2 = Setting(key="daily_review_limit", value=100)
        test_db.add_all([setting1, setting2])
        test_db.commit()

        # Act - update only one setting
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": 30}
        )

        # Assert - should return all settings
        data = response.json()["data"]
        assert data["daily_new_limit"] == 30
        assert data["daily_review_limit"] == 100

    def test_update_settings_persists_changes(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings persists changes to database."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": 30}
        )

        # Assert - changes should persist
        assert response.status_code == 200

        # Verify with GET
        get_response = client.get("/api/v1/settings")
        data = get_response.json()["data"]
        assert data["daily_new_limit"] == 30

    def test_update_settings_with_source_scope(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings can update default_source_scope."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"default_source_scope": [1, 2, 3]}
        )

        # Assert
        data = response.json()["data"]
        assert data["default_source_scope"] == [1, 2, 3]

    def test_update_settings_with_empty_source_scope(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings accepts empty list for default_source_scope."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"default_source_scope": []}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["default_source_scope"] == []

    def test_update_settings_ignores_none_values(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings ignores None values in request."""
        # Arrange
        from app.models import Setting

        setting = Setting(key="daily_new_limit", value=20)
        test_db.add(setting)
        test_db.commit()

        # Act - send None for review_limit (should be ignored)
        response = client.put(
            "/api/v1/settings",
            json={
                "daily_new_limit": 30,
                "daily_review_limit": None
            }
        )

        # Assert - should only update daily_new_limit
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["daily_new_limit"] == 30

    # Validation error tests

    def test_update_settings_rejects_invalid_key(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings returns 400 for invalid setting key."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"invalid_key": 123}
        )

        # Assert
        assert response.status_code == 400

    def test_update_settings_invalid_key_error_structure(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings returns proper error structure for invalid key."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"invalid_key": 123}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()

        assert "detail" in data
        detail = data["detail"]
        assert "request_id" in detail
        assert "error" in detail

        error = detail["error"]
        assert "code" in error
        assert "message" in error
        assert error["code"] == "INVALID_SETTINGS"

    def test_update_settings_negative_daily_new_limit(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings rejects negative daily_new_limit."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": -10}
        )

        # Assert
        assert response.status_code == 400
        error = response.json()["detail"]["error"]
        assert error["code"] == "INVALID_SETTINGS"
        assert "non-negative integer" in error["message"]

    def test_update_settings_negative_daily_review_limit(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings rejects negative daily_review_limit."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_review_limit": -50}
        )

        # Assert
        assert response.status_code == 400
        error = response.json()["detail"]["error"]
        assert error["code"] == "INVALID_SETTINGS"

    def test_update_settings_invalid_type_daily_new_limit(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings rejects non-integer daily_new_limit."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"daily_new_limit": "twenty"}
        )

        # Assert - should fail at validation level (422) or business logic level (400)
        assert response.status_code in [400, 422]

    def test_update_settings_invalid_type_source_scope(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings rejects non-list default_source_scope."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={"default_source_scope": "1,2,3"}
        )

        # Assert - should fail at validation level (422) or business logic level (400)
        assert response.status_code in [400, 422]

    def test_update_settings_allows_zero_limits(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings allows zero as valid limit value."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={
                "daily_new_limit": 0,
                "daily_review_limit": 0
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["daily_new_limit"] == 0
        assert data["daily_review_limit"] == 0

    def test_update_settings_empty_request_body(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings handles empty request body."""
        # Act
        response = client.put(
            "/api/v1/settings",
            json={}
        )

        # Assert - should succeed but not change anything
        assert response.status_code == 200

    def test_update_settings_content_type_json(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings requires JSON content type."""
        # Act
        response = client.put(
            "/api/v1/settings",
            data="daily_new_limit=30",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - should reject non-JSON content
        assert response.status_code == 422

    def test_update_settings_malformed_json(self, client: TestClient, test_db: Session):
        """Test PUT /api/v1/settings rejects malformed JSON."""
        # Act
        response = client.put(
            "/api/v1/settings",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422

    def test_update_settings_complete_workflow(self, client: TestClient, test_db: Session):
        """Test complete settings update workflow: create, update, verify."""
        # Step 1: Create initial settings
        response1 = client.put(
            "/api/v1/settings",
            json={
                "daily_new_limit": 20,
                "daily_review_limit": 100,
                "default_source_scope": [1]
            }
        )
        assert response1.status_code == 200

        # Step 2: Update some settings
        response2 = client.put(
            "/api/v1/settings",
            json={
                "daily_new_limit": 30,
                "default_source_scope": [1, 2, 3]
            }
        )
        assert response2.status_code == 200

        # Step 3: Verify final state
        response3 = client.get("/api/v1/settings")
        data = response3.json()["data"]

        assert data["daily_new_limit"] == 30  # Updated
        assert data["daily_review_limit"] == 100  # Unchanged
        assert data["default_source_scope"] == [1, 2, 3]  # Updated
