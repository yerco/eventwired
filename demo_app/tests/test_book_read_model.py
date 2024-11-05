import pytest
import fakeredis.aioredis

from src.services.redis_service import RedisService

from demo_app.models.book_read_model import BookReadModel


# Fixture to create a RedisService instance with fake Redis
@pytest.fixture
async def redis_service():
    # Create an in-memory Redis client using fakeredis
    fake_redis = await fakeredis.aioredis.FakeRedis()
    service = RedisService(redis_client=fake_redis)
    yield service
    await fake_redis.aclose()  # Use aclose() to properly close the connection
    await fake_redis.connection_pool.disconnect()  # Ensure all connections are closed


# Fixture to create a BookReadModel instance
@pytest.fixture
async def book_read_model(redis_service: RedisService):
    return BookReadModel(redis_service=redis_service)


# Test the `add_book` method
@pytest.mark.asyncio
async def test_add_book(book_read_model: BookReadModel):
    book_data = {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_date": "1925-04-10",
        "isbn": "9780743273565",
        "stock_quantity": "10"
    }
    await book_read_model.add_book(title=book_data["title"], book_data=book_data)

    # Verify that the book was added
    added_book = await book_read_model.get_book("The Great Gatsby")
    assert added_book == book_data


# Test the `update_book` method
@pytest.mark.asyncio
async def test_update_book(book_read_model: BookReadModel):
    book_data = {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_date": "1925-04-10",
        "isbn": "9780743273565",
        "stock_quantity": "10"
    }
    await book_read_model.add_book(title=book_data["title"], book_data=book_data)

    # Update the book
    updated_data = {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_date": "1925-04-10",
        "isbn": "9780743273565",
        "stock_quantity": "15"  # Updated stock quantity
    }
    await book_read_model.update_book(title=book_data["title"], updated_data=updated_data)

    # Verify that the book was updated
    updated_book = await book_read_model.get_book("The Great Gatsby")
    assert updated_book == updated_data


# Test the `delete_book` method
@pytest.mark.asyncio
async def test_delete_book(book_read_model: BookReadModel):
    book_data = {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_date": "1925-04-10",
        "isbn": "9780743273565",
        "stock_quantity": "10"
    }
    await book_read_model.add_book(title=book_data["title"], book_data=book_data)

    # Delete the book
    await book_read_model.delete_book(title=book_data["title"])

    # Verify that the book was deleted
    deleted_book = await book_read_model.get_book("The Great Gatsby")
    assert deleted_book is None


# Test the `get_book` method
@pytest.mark.asyncio
async def test_get_book(book_read_model: BookReadModel):
    book_data = {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_date": "1925-04-10",
        "isbn": "9780743273565",
        "stock_quantity": "10"
    }
    await book_read_model.add_book(title=book_data["title"], book_data=book_data)

    # Get the book and verify the details
    retrieved_book = await book_read_model.get_book("The Great Gatsby")
    assert retrieved_book == book_data


# Test the `list_all_books` method
@pytest.mark.asyncio
async def test_list_all_books(book_read_model: BookReadModel):
    book_data_1 = {
        "id": "1",
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "published_date": "1925-04-10",
        "isbn": "9780743273565",
        "stock_quantity": "10"
    }
    book_data_2 = {
        "id": "2",
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "published_date": "1960-07-11",
        "isbn": "9780060935467",
        "stock_quantity": "8"
    }
    await book_read_model.add_book(title=book_data_1["title"], book_data=book_data_1)
    await book_read_model.add_book(title=book_data_2["title"], book_data=book_data_2)

    # List all books and verify the details
    all_books = await book_read_model.list_all_books()
    assert len(all_books) == 2
    assert book_data_1 in all_books
    assert book_data_2 in all_books
