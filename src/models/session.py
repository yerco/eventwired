import datetime
from sqlalchemy import Column, String, Text, DateTime

from src.models.base import Base


class Session(Base):
    __tablename__ = 'session'
    session_id = Column(String(255), primary_key=True)
    session_data = Column(Text, nullable=False)  # This could be a JSON field or serialized text
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
