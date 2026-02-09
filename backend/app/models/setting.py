"""System settings model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from app.database import Base


class Setting(Base):
    """System configuration settings.

    Uses key-value store pattern with JSON for complex values.
    """

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
