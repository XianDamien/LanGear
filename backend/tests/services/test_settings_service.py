"""
Unit tests for SettingsService.

Tests business logic for settings management.
"""

import pytest
from sqlalchemy.orm import Session
from app.services.settings_service import SettingsService
from tests.test_data.seed_data import create_test_settings


@pytest.mark.unit
class TestSettingsService:
    """Test SettingsService business logic."""

    def test_get_settings_empty(self, test_db: Session):
        """Test getting settings when none exist."""
        service = SettingsService(test_db)
        result = service.get_settings()

        assert isinstance(result, dict)
        assert result == {}

    def test_get_settings_with_data(self, test_db: Session):
        """Test getting settings with existing supported data."""
        create_test_settings(test_db)

        service = SettingsService(test_db)
        result = service.get_settings()

        assert "daily_new_limit" in result
        assert "daily_review_limit" in result
        assert "max_interval" not in result
        assert "enable_audio" not in result
        assert result["daily_new_limit"] == 20
        assert result["daily_review_limit"] == 50

    def test_get_settings_filters_legacy_app_timezone_key(self, test_db: Session):
        """Test removed app_timezone is not exposed in read responses."""
        from app.models import Setting

        test_db.add_all(
            [
                Setting(key="daily_new_limit", value=20),
                Setting(key="app_timezone", value="Europe/Budapest"),
            ]
        )
        test_db.commit()

        service = SettingsService(test_db)
        result = service.get_settings()

        assert result == {"daily_new_limit": 20}

    def test_update_settings_success(self, test_db: Session):
        """Test updating settings with valid data."""
        create_test_settings(test_db)

        service = SettingsService(test_db)
        updates = {
            "daily_new_limit": 30,
            "daily_review_limit": 150
        }

        result = service.update_settings(updates)

        assert result["daily_new_limit"] == 30
        assert result["daily_review_limit"] == 150

    def test_update_settings_invalid_key(self, test_db: Session):
        """Test updating settings with invalid key."""
        service = SettingsService(test_db)
        updates = {
            "invalid_key": 123
        }

        with pytest.raises(ValueError, match="Invalid settings keys"):
            service.update_settings(updates)

    def test_update_settings_invalid_daily_new_limit(self, test_db: Session):
        """Test updating daily_new_limit with invalid value."""
        service = SettingsService(test_db)

        # Test negative value
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            service.update_settings({"daily_new_limit": -1})

        # Test non-integer
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            service.update_settings({"daily_new_limit": "twenty"})

    def test_update_settings_invalid_daily_review_limit(self, test_db: Session):
        """Test updating daily_review_limit with invalid value."""
        service = SettingsService(test_db)

        # Test negative value
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            service.update_settings({"daily_review_limit": -10})

        # Test float
        with pytest.raises(ValueError, match="must be a non-negative integer"):
            service.update_settings({"daily_review_limit": 10.5})

    def test_update_settings_invalid_source_scope(self, test_db: Session):
        """Test updating default_source_scope with invalid value."""
        service = SettingsService(test_db)

        # Test non-list
        with pytest.raises(ValueError, match="must be a list"):
            service.update_settings({"default_source_scope": 123})

    def test_update_settings_valid_source_scope(self, test_db: Session):
        """Test updating default_source_scope with valid list."""
        service = SettingsService(test_db)
        updates = {
            "default_source_scope": [1, 2, 3]
        }

        result = service.update_settings(updates)

        assert result["default_source_scope"] == [1, 2, 3]

    def test_update_settings_multiple_keys(self, test_db: Session):
        """Test updating multiple settings at once."""
        create_test_settings(test_db)

        service = SettingsService(test_db)
        updates = {
            "daily_new_limit": 25,
            "daily_review_limit": 75,
            "default_source_scope": [1]
        }

        result = service.update_settings(updates)

        assert result["daily_new_limit"] == 25
        assert result["daily_review_limit"] == 75
        assert result["default_source_scope"] == [1]

    def test_update_settings_zero_values(self, test_db: Session):
        """Test updating settings with zero values (valid)."""
        service = SettingsService(test_db)
        updates = {
            "daily_new_limit": 0,
            "daily_review_limit": 0
        }

        result = service.update_settings(updates)

        assert result["daily_new_limit"] == 0
        assert result["daily_review_limit"] == 0

    def test_update_settings_rejects_app_timezone_key(self, test_db: Session):
        """Test app_timezone is no longer a supported setting key."""
        service = SettingsService(test_db)

        with pytest.raises(ValueError, match="Invalid settings keys"):
            service.update_settings({"app_timezone": "Europe/Budapest"})
