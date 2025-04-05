from sqlalchemy import Column, Integer, String, Boolean

from src.models.base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, nullable=False, default=False)
