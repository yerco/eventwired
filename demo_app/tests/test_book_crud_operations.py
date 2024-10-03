import os
import pytest
from datetime import date

from src.services.orm.orm_service import ORMService
from src.services.config_service import ConfigService
from src.models.base import Base

from demo_app.models.book import Book


@pytest.fixture(scope="function")
async def orm_service():
    config_service = ConfigService()
    db_file = 'a_default.db'
    config_service.set('DATABASE_URL', f'sqlite+aiosqlite:///{db_file}')
    orm_service = ORMService(config_service, Base=Base)
    await orm_service.init()
    await orm_service.create_tables()  # Ensure tables are created before each test
    yield orm_service
    await orm_service.cleanup()

    # Ensure the database file is deleted after the tests
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.mark.asyncio
async def test_create_book(orm_service):
    # Create a new book record
    book = await orm_service.create(
        Book,
        title="Test Book",
        author="Test Author",
        published_date=date(2024, 1, 1),
        isbn="1234567890",
        stock_quantity=10
    )
    assert book is not None, "The book should be created successfully"
    assert book.title == "Test Book", "The book title should be 'Test Book'"


@pytest.mark.asyncio
async def test_get_book_by_id(orm_service):
    # Create a book to retrieve
    created_book = await orm_service.create(
        Book,
        title="Retrieve Book",
        author="Author Name",
        published_date=date(2023, 12, 1),
        isbn="0987654321",
        stock_quantity=5
    )
    # Retrieve the book by its primary key
    retrieved_book = await orm_service.get(Book, lookup_value=created_book.id)
    assert retrieved_book is not None, "The book should be retrieved successfully"
    assert retrieved_book.title == "Retrieve Book", "The book title should match the created title"


@pytest.mark.asyncio
async def test_get_book_by_title(orm_service):
    # Create a book to retrieve by title
    created_book = await orm_service.create(
        Book,
        title="Unique Title",
        author="Special Author",
        published_date=date(2022, 11, 1),
        isbn="1122334455",
        stock_quantity=3
    )
    # Retrieve the book by title
    retrieved_book = await orm_service.get(Book, lookup_value="Unique Title", lookup_column="title")
    assert retrieved_book is not None, "The book should be retrieved by its title"
    assert retrieved_book.title == "Unique Title", "The book title should match the queried title"


@pytest.mark.asyncio
async def test_update_book(orm_service):
    # Create a book to update
    created_book = await orm_service.create(
        Book,
        title="Old Title",
        author="Original Author",
        published_date=date(2021, 1, 1),
        isbn="2233445566",
        stock_quantity=7
    )
    # Update the book title
    updated_book = await orm_service.update(
        Book,
        lookup_value=created_book.id,
        lookup_column="id",
        title="Updated Title",
        return_instance=True
    )
    assert updated_book is not None, "The book should be updated successfully"
    assert updated_book.title == "Updated Title", "The book title should be updated to 'Updated Title'"


@pytest.mark.asyncio
async def test_delete_book(orm_service):
    # Create a book to delete
    book_to_delete = await orm_service.create(
        Book,
        title="Book to Delete",
        author="Delete Author",
        published_date=date(2020, 6, 1),
        isbn="6677889900",
        stock_quantity=1
    )
    # Delete the book by its primary key
    await orm_service.delete(Book, lookup_value=book_to_delete.id)
    # Verify the book has been deleted
    deleted_book = await orm_service.get(Book, lookup_value=book_to_delete.id)
    assert deleted_book is None, "The book should be deleted successfully"


@pytest.mark.asyncio
async def test_get_all_books(orm_service):
    # Clear all books from the database
    await orm_service.delete(Book, lookup_value="title")

    # Create multiple books
    await orm_service.create(Book, title="Book 1", author="Author 1", published_date=date(2021, 1, 1))
    await orm_service.create(Book, title="Book 2", author="Author 2", published_date=date(2022, 2, 2))

    # Retrieve all books
    all_books = await orm_service.all(Book)
    assert len(all_books) == 2, "There should be two books in the database"
    assert {book.title for book in all_books} == {"Book 1", "Book 2"}, "The titles should match the created books"
