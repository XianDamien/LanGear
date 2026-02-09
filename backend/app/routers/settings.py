"""Settings router for system configuration."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


class SettingsUpdateRequest(BaseModel):
    """Request model for updating settings."""

    daily_new_limit: int | None = None
    daily_review_limit: int | None = None
    default_source_scope: list[int] | None = None


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    """Get all system settings.

    Returns:
        Response with settings:
        - request_id: Unique request ID
        - data: Dictionary of all settings

    Example response:
        {
            "request_id": "...",
            "data": {
                "daily_new_limit": 20,
                "daily_review_limit": 100,
                "default_source_scope": [1, 2]
            }
        }
    """
    request_id = str(uuid.uuid4())

    settings_service = SettingsService(db)
    settings = settings_service.get_settings()

    return {
        "request_id": request_id,
        "data": settings,
    }


@router.put("")
def update_settings(
    request: SettingsUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update system settings.

    Args:
        request: Settings update request

    Returns:
        Response with updated settings:
        - request_id: Unique request ID
        - data: Dictionary of all updated settings

    Raises:
        400: If invalid settings provided
    """
    request_id = str(uuid.uuid4())

    try:
        # Convert request to dict, excluding None values
        updates = {
            k: v for k, v in request.model_dump().items() if v is not None
        }

        settings_service = SettingsService(db)
        updated_settings = settings_service.update_settings(updates)

        return {
            "request_id": request_id,
            "data": updated_settings,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "request_id": request_id,
                "error": {
                    "code": "INVALID_SETTINGS",
                    "message": str(e),
                },
            },
        )
