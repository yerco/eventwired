from sqlalchemy import Column, Integer, String, Date

from src.models.base import Base


class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    published_date = Column(Date, nullable=True)
    isbn = Column(String, unique=True, nullable=True)
    stock_quantity = Column(Integer, default=0)
