from sqlalchemy import Column, Integer, String, func, DateTime, Text

from src.models.base import Base


class EventLog(Base):
    __tablename__ = 'event_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(255), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    additional_data = Column(Text, nullable=True)
