import pytest
from unittest.mock import AsyncMock, patch
from datetime import date

from demo_app.handlers.book_handlers import BookCommandHandler
from demo_app.models.book import Book

from src.services.orm.orm_service import ORMService
from src.services.redis_service import RedisService

# Fixtures for mocks
@pytest.fixture
def orm_service_mock():
    return AsyncMock(spec=ORMService)


@pytest.fixture
def redis_service_mock():
    return AsyncMock(spec=RedisService)


@pytest.fixture
def command_handler_with_redis(orm_service_mock, redis_service_mock):
    return BookCommandHandler(orm_service=orm_service_mock, redis_service=redis_service_mock)


@pytest.fixture
def command_handler_without_redis(orm_service_mock):
    return BookCommandHandler(orm_service=orm_service_mock, redis_service=None)


# Tests for `add_book`
@pytest.mark.asyncio
async def test_add_book_success_with_redis(command_handler_with_redis, orm_service_mock, redis_service_mock):
    orm_service_mock.get.return_value = None
    orm_service_mock.create.return_value = Book(
        id=1,
        title="Test Book",
        author="Test Author",
        published_date=date(2024, 1, 1),
        isbn="1234567890",
        stock_quantity=10
    )

    result = await command_handler_with_redis.add_book(
        title="Test Book",
        author="Test Author",
        published_date="2024-01-01",
        isbn="1234567890",
        stock_quantity="10"
    )

    assert result["status"] == "success"
    assert redis_service_mock.set_session.called


@pytest.mark.asyncio
async def test_add_book_success_without_redis(command_handler_without_redis, orm_service_mock):
    orm_service_mock.get.return_value = None
    orm_service_mock.create.return_value = Book(
        id=1,
        title="Test Book",
        author="Test Author",
        published_date=date(2024, 1, 1),
        isbn="1234567890",
        stock_quantity=10
    )

    result = await command_handler_without_redis.add_book(
        title="Test Book",
        author="Test Author",
        published_date="2024-01-01",
        isbn="1234567890",
        stock_quantity="10"
    )

    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_add_book_duplicate_title(command_handler_with_redis, orm_service_mock):
    orm_service_mock.get.return_value = Book(
        id=1,
        title="Test Book",
        author="Test Author"
    )

    result = await command_handler_with_redis.add_book(
        title="Test Book",
        author="Test Author"
    )

    assert result["status"] == "error"
    assert result["message"] == "A book with this title and author already exists."


@pytest.mark.asyncio
async def test_add_book_invalid_published_date(command_handler_with_redis):
    result = await command_handler_with_redis.add_book(
        title="Test Book",
        author="Test Author",
        published_date="invalid-date"
    )

    assert result["status"] == "error"
    assert result["message"] == "Published date must be in the format YYYY-MM-DD."


# Tests for `update_book`
@pytest.mark.asyncio
async def test_update_book_success_with_redis(command_handler_with_redis, orm_service_mock, redis_service_mock):
    orm_service_mock.update.return_value = Book(
        id=1,
        title="Updated Book",
        author="Updated Author",
        published_date=date(2024, 1, 1),
        isbn="1234567890",
        stock_quantity=15
    )

    result = await command_handler_with_redis.update_book(
        title="Test Book",
        new_title="Updated Book",
        author="Updated Author",
        published_date="2024-01-01",
        isbn="1234567890",
        stock_quantity="15"
    )

    assert result is True
    assert redis_service_mock.set_session.called


@pytest.mark.asyncio
async def test_update_book_not_found(command_handler_with_redis, orm_service_mock):
    orm_service_mock.update.return_value = None

    with pytest.raises(ValueError, match="Book with title 'Test Book' not found."):
        await command_handler_with_redis.update_book(
            title="Test Book",
            new_title="Updated Book",
            author="Updated Author"
        )


# Tests for `delete_book`
@pytest.mark.asyncio
async def test_delete_book_success_with_redis(command_handler_with_redis, orm_service_mock, redis_service_mock):
    # Arrange: Set up the mocks
    orm_service_mock.delete.return_value = True

    # Mocking the RedisService client delete method
    redis_service_mock.client = AsyncMock()  # Adding a mock client attribute to RedisService
    redis_service_mock.client.delete.return_value = None  # Mocking the delete method on the client

    # Act: Call the delete_book method
    result = await command_handler_with_redis.delete_book(title="Test Book")

    # Assert: Ensure the book was deleted and the cache was updated
    assert result["status"] == "success"
    redis_service_mock.client.delete.assert_called_once_with("book:Test Book")


@pytest.mark.asyncio
async def test_delete_book_not_found(command_handler_with_redis, orm_service_mock):
    orm_service_mock.delete.return_value = False

    with pytest.raises(ValueError, match="Book with title 'Test Book' not found."):
        await command_handler_with_redis.delete_book(title="Test Book")


@pytest.mark.asyncio
async def test_delete_book_validation_error(command_handler_with_redis):
    with pytest.raises(ValueError, match="At least one of 'title' or 'author' must be provided to delete a book."):
        await command_handler_with_redis.delete_book()


# READ section
