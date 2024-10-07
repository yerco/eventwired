import pytest
import datetime
from unittest.mock import AsyncMock

from demo_app.handlers.book_handlers import BookQueryHandler
from demo_app.models.book import Book


# Fixtures
@pytest.fixture
def orm_service_mock():
    return AsyncMock()

@pytest.fixture
def redis_service_mock():
    return AsyncMock()

@pytest.fixture
def query_handler_with_redis(orm_service_mock, redis_service_mock):
    return BookQueryHandler(orm_service=orm_service_mock, redis_service=redis_service_mock)

@pytest.fixture
def query_handler_without_redis(orm_service_mock):
    return BookQueryHandler(orm_service=orm_service_mock)


# Tests for BookQueryHandler (Read Section)
@pytest.mark.asyncio
async def test_get_book_by_isbn_with_redis(query_handler_with_redis, redis_service_mock):
    # Mock Redis get to return a book
    redis_service_mock.get_session.return_value = {
        "id": "1",
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890",
        "published_date": "2024-01-01",
        "stock_quantity": "10"
    }

    book = await query_handler_with_redis.get_book_by_isbn("1234567890")

    redis_service_mock.get_session.assert_awaited_once_with("book:1234567890")
    assert book["title"] == "Test Book"
    assert book["isbn"] == "1234567890"


@pytest.mark.asyncio
async def test_get_book_by_isbn_without_redis(query_handler_without_redis, orm_service_mock):
    # Mock ORM get to return a Book instance
    book_instance = Book(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        published_date="2024-01-01",
        stock_quantity=10
    )
    orm_service_mock.get.return_value = book_instance

    book = await query_handler_without_redis.get_book_by_isbn("1234567890")

    orm_service_mock.get.assert_awaited_once_with(Book, lookup_value="1234567890", lookup_column="isbn")
    assert book.title == "Test Book"
    assert book.isbn == "1234567890"


@pytest.mark.asyncio
async def test_list_all_books_with_redis(query_handler_with_redis, redis_service_mock):
    # Mock Redis to return a list of books
    redis_service_mock.client.keys.return_value = ["book:Test Book"]
    redis_service_mock.get_session.return_value = {
        "id": "1",
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890",
        "published_date": "2024-01-01",
        "stock_quantity": "10"
    }

    books = await query_handler_with_redis.list_all_books()

    redis_service_mock.client.keys.assert_awaited_once_with("book:*")
    redis_service_mock.get_session.assert_awaited_once_with("book:Test Book")
    assert len(books) == 1
    assert books[0]["title"] == "Test Book"


@pytest.mark.asyncio
async def test_list_all_books_without_redis(query_handler_without_redis, orm_service_mock):
    # Mock ORM to return a list of Book instances
    book_instance = Book(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        published_date="2024-01-01",
        stock_quantity=10
    )
    orm_service_mock.all.return_value = [book_instance]

    books = await query_handler_without_redis.list_all_books()

    orm_service_mock.all.assert_awaited_once_with(Book)
    assert len(books) == 1
    assert books[0].title == "Test Book"


@pytest.mark.asyncio
async def test_find_books_by_author_with_redis(query_handler_with_redis, redis_service_mock):
    # Mock Redis to return books by a specific author
    redis_service_mock.client.keys.return_value = ["book:Test Book"]
    redis_service_mock.get_session.return_value = {
        "id": "1",
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890",
        "published_date": "2024-01-01",
        "stock_quantity": "10"
    }

    books = await query_handler_with_redis.find_books_by_author("Test Author")

    redis_service_mock.client.keys.assert_awaited_once_with("book:*")
    redis_service_mock.get_session.assert_awaited_once_with("book:Test Book")
    assert len(books) == 1
    assert books[0]["author"] == "Test Author"


@pytest.mark.asyncio
async def test_find_books_by_author_without_redis(query_handler_without_redis, orm_service_mock):
    # Mock ORM to return a list of books
    book_instance = Book(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        published_date="2024-01-01",
        stock_quantity=10
    )
    orm_service_mock.all.return_value = [book_instance]

    books = await query_handler_without_redis.find_books_by_author("Test Author")

    orm_service_mock.all.assert_awaited_once_with(Book)
    assert len(books) == 1
    assert books[0].author == "Test Author"


@pytest.mark.asyncio
async def test_find_books_published_after_with_redis(query_handler_with_redis, redis_service_mock):
    # Mock Redis to return books published after a certain year
    redis_service_mock.client.keys.return_value = ["book:Test Book"]
    redis_service_mock.get_session.return_value = {
        "id": "1",
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890",
        "published_date": "2024-01-01",
        "stock_quantity": "10"
    }

    books = await query_handler_with_redis.find_books_published_after(2020)

    redis_service_mock.client.keys.assert_awaited_once_with("book:*")
    redis_service_mock.get_session.assert_awaited_once_with("book:Test Book")
    assert len(books) == 1
    assert books[0]["published_date"] == "2024-01-01"


@pytest.mark.asyncio
async def test_find_books_published_after_without_redis(query_handler_without_redis, orm_service_mock):
    # Mock ORM to return a list of books
    book_instance = Book(
        id=1,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
        published_date=datetime.date(2024, 1, 1),  # Use a datetime.date object here
        stock_quantity=10
    )
    orm_service_mock.all.return_value = [book_instance]

    books = await query_handler_without_redis.find_books_published_after(2020)

    orm_service_mock.all.assert_awaited_once_with(Book)
    assert len(books) == 1
    assert books[0].published_date.year == 2024
