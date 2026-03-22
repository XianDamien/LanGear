"""User model."""

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base
from app.utils.timezone import storage_now


class User(Base):
    """User account model (MVP: single admin user with ID=1)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime, default=storage_now, nullable=False)
    updated_at = Column(DateTime, default=storage_now, onupdate=storage_now, nullable=False)
