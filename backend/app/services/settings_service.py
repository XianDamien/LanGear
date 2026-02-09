"""Settings service for system configuration."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories.settings_repo import SettingsRepository


class SettingsService:
    """Service for managing system settings."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.db = db
        self.settings_repo = SettingsRepository(db)

    def get_settings(self) -> dict[str, Any]:
        """Get all system settings.

        Returns:
            Dictionary with all settings key-value pairs

        Example:
            {
                "daily_new_limit": 20,
                "daily_review_limit": 100,
                "default_source_scope": [1, 2]
            }
        """
        return self.settings_repo.get_all()

    def update_settings(self, updates: dict[str, Any]) -> dict[str, Any]:
        """Update system settings.

        Args:
            updates: Dictionary of settings to update

        Returns:
            Updated settings dictionary

        Raises:
            ValueError: If invalid settings provided
        """
        # Validate settings
        valid_keys = {"daily_new_limit", "daily_review_limit", "default_source_scope"}

        invalid_keys = set(updates.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid settings keys: {invalid_keys}")

        # Validate daily limits
        if "daily_new_limit" in updates:
            if not isinstance(updates["daily_new_limit"], int) or updates["daily_new_limit"] < 0:
                raise ValueError("daily_new_limit must be a non-negative integer")

        if "daily_review_limit" in updates:
            if not isinstance(updates["daily_review_limit"], int) or updates["daily_review_limit"] < 0:
                raise ValueError("daily_review_limit must be a non-negative integer")

        # Validate source scope
        if "default_source_scope" in updates:
            if not isinstance(updates["default_source_scope"], list):
                raise ValueError("default_source_scope must be a list")

        # Update settings
        for key, value in updates.items():
            self.settings_repo.set(key, value)

        self.db.commit()

        return self.settings_repo.get_all()
