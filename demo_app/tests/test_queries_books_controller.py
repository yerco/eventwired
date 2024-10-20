from datetime import date

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

from demo_app.forms.book_form import BookForm
from src.core.event_bus import Event

from demo_app.controllers.queries_books_controller import queries_books_controller
from demo_app.models.book import Book


@pytest.fixture
def event_list_books():
    # Fixture for the event representing a GET /books request
    request_mock = AsyncMock()
    request_mock.method = "GET"
    request_mock.path = "/books"
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.fixture
def event_book_detail():
    request_mock = AsyncMock()
    request_mock.method = "GET"
    request_mock.path = "/books/Test%20Book"
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.fixture
def event_edit_book():
    request_mock = AsyncMock()
    request_mock.method = "GET"
    request_mock.path = "/books/Test%20Book/edit"
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.mark.asyncio
async def test_list_books(event_list_books, monkeypatch):
    # Arrange
    form_service_mock = AsyncMock()
    template_service_mock = Mock()
    template_service_mock.render_template.return_value = "Rendered Content"
    orm_service_mock = AsyncMock()
    orm_service_mock.all.return_value = [
        Book(title="Book 1", author="Author 1"),
        Book(title="Book 2", author="Author 2")
    ]

    # Mock query handler and its method
    query_handler_mock = AsyncMock()
    query_handler_mock.list_all_books.return_value = orm_service_mock.all.return_value
    redis_service_mock = None

    # Use monkeypatch to replace dependencies in the DI container
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(side_effect=[form_service_mock, template_service_mock, orm_service_mock, redis_service_mock]))

    # Use monkeypatch to replace BookQueryHandler with our mocked query_handler
    monkeypatch.setattr('demo_app.controllers.queries_books_controller.BookQueryHandler', lambda *args, **kwargs: query_handler_mock)

    # Act
    await queries_books_controller(event_list_books)

    # Assert
    query_handler_mock.list_all_books.assert_awaited_once()  # Ensure list_all_books was awaited exactly once
    template_service_mock.render_template.assert_called_once()

    # Get the actual call argument to compare its values
    actual_call = template_service_mock.render_template.call_args
    actual_args, actual_kwargs = actual_call

    # Extract the books list from the positional arguments (since the first argument is the template name)
    actual_context = actual_args[1] if len(actual_args) > 1 else actual_kwargs.get('context')

    # Extract books from the context
    actual_books = actual_context['books']

    # Compare attributes instead of the objects themselves
    expected_books = [
        {"title": "Book 1", "author": "Author 1"},
        {"title": "Book 2", "author": "Author 2"}
    ]

    for actual_book, expected_book in zip(actual_books, expected_books):
        assert actual_book.title == expected_book["title"]
        assert actual_book.author == expected_book["author"]


@pytest.mark.asyncio
async def test_list_books_with_redis(event_list_books, monkeypatch):
    # Arrange
    form_service_mock = AsyncMock()
    template_service_mock = Mock()
    template_service_mock.render_template.return_value = "Rendered Content"
    orm_service_mock = AsyncMock()
    redis_service_mock = AsyncMock()

    # Mock Redis interactions in BookReadModel
    book_read_model_mock = AsyncMock()
    book_read_model_mock.list_all_books.return_value = [
        {"title": "Book 1", "author": "Author 1"},
        {"title": "Book 2", "author": "Author 2"}
    ]

    # Mock BookQueryHandler to include the mocked BookReadModel
    class MockBookQueryHandler:
        def __init__(self, *args, **kwargs):
            self.book_read_model = book_read_model_mock

        async def list_all_books(self):
            return await self.book_read_model.list_all_books()

    # Use monkeypatch to replace dependencies in the DI container
    monkeypatch.setattr(
        'demo_app.di_setup.di_container.get',
        AsyncMock(side_effect=[form_service_mock, template_service_mock, orm_service_mock, redis_service_mock])
    )

    # Use monkeypatch to replace BookQueryHandler with our mocked handler class
    monkeypatch.setattr(
        'demo_app.controllers.queries_books_controller.BookQueryHandler',
        MockBookQueryHandler
    )

    # Act
    await queries_books_controller(event_list_books)

    # Assert
    book_read_model_mock.list_all_books.assert_awaited_once()  # Ensure list_all_books was awaited exactly once
    template_service_mock.render_template.assert_called_once()

    # Get the actual call argument to compare its values
    actual_call = template_service_mock.render_template.call_args
    actual_args, actual_kwargs = actual_call

    # Extract the books list from the positional arguments (since the first argument is the template name)
    actual_context = actual_args[1] if len(actual_args) > 1 else actual_kwargs.get('context')

    # Extract books from the context
    actual_books = actual_context['books']

    # Compare attributes instead of the objects themselves
    expected_books = [
        {"title": "Book 1", "author": "Author 1"},
        {"title": "Book 2", "author": "Author 2"}
    ]

    for actual_book, expected_book in zip(actual_books, expected_books):
        assert actual_book["title"] == expected_book["title"]
        assert actual_book["author"] == expected_book["author"]


@pytest.mark.asyncio
async def test_book_detail(event_book_detail, monkeypatch):
    # Arrange
    form_service_mock = AsyncMock()
    template_service_mock = Mock()  # Mocking template service to be synchronous
    template_service_mock.render_template.return_value = "Rendered Content"
    orm_service_mock = AsyncMock()
    orm_service_mock.get.return_value = Book(
        title="Test Book",
        author="Test Author",
        published_date=date(2024, 1, 1),
        isbn="1234567890",
        stock_quantity=10
    )
    redis_service_mock = None

    # Mock query handler and its method
    query_handler_mock = AsyncMock()
    query_handler_mock.get_book_by_title.return_value = orm_service_mock.get.return_value

    # Use monkeypatch to replace dependencies in the DI container
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(side_effect=[form_service_mock, template_service_mock, orm_service_mock, redis_service_mock]))

    # Use monkeypatch to replace BookQueryHandler with our mocked query_handler
    monkeypatch.setattr('demo_app.controllers.queries_books_controller.BookQueryHandler', lambda *args, **kwargs: query_handler_mock)

    # Act
    await queries_books_controller(event_book_detail)

    # Assert
    query_handler_mock.get_book_by_title.assert_awaited_once_with("Test Book")  # Ensure the correct book was queried
    template_service_mock.render_template.assert_called_once()

    # Get the actual call arguments to compare their values
    actual_call = template_service_mock.render_template.call_args
    actual_args, actual_kwargs = actual_call

    # Extract the context from the positional arguments (since the first argument is the template name)
    actual_context = actual_args[1] if len(actual_args) > 1 else actual_kwargs.get('context')

    # Extract book from the context
    actual_book = actual_context['book']

    # Compare attributes instead of the objects themselves
    assert actual_book.title == "Test Book"
    assert actual_book.author == "Test Author"
    assert str(actual_book.published_date) == "2024-01-01"  # Comparing dates as strings for simplicity
    assert actual_book.isbn == "1234567890"
    assert actual_book.stock_quantity == 10

    # Assert that the template was called with the expected context
    expected_context = {
        "book": orm_service_mock.get.return_value,
        "csrf_token": "dummy_csrf_token",
    }
    template_service_mock.render_template.assert_called_once_with(
        'book_detail.html', expected_context
    )


@pytest.mark.asyncio
async def test_book_detail_with_redis(event_book_detail, monkeypatch):
    # Arrange
    form_service_mock = AsyncMock()
    template_service_mock = Mock()  # Mocking template service to be synchronous
    template_service_mock.render_template.return_value = "Rendered Content"
    orm_service_mock = AsyncMock()
    redis_service_mock = AsyncMock()

    # Mock Redis interactions in BookReadModel
    book_read_model_mock = AsyncMock()
    book_read_model_mock.get_book.return_value = {
        "title": "Test Book",
        "author": "Test Author",
        "published_date": "2024-01-01",
        "isbn": "1234567890",
        "stock_quantity": "10"
    }

    # Mock BookQueryHandler to include the mocked BookReadModel
    class MockBookQueryHandler:
        def __init__(self, *args, **kwargs):
            self.book_read_model = book_read_model_mock

        async def get_book_by_title(self, title: str):
            return await self.book_read_model.get_book(title)

    # Use monkeypatch to replace dependencies in the DI container
    monkeypatch.setattr(
        'demo_app.di_setup.di_container.get',
        AsyncMock(side_effect=[form_service_mock, template_service_mock, orm_service_mock, redis_service_mock])
    )

    # Use monkeypatch to replace BookQueryHandler with our mocked handler class
    monkeypatch.setattr(
        'demo_app.controllers.queries_books_controller.BookQueryHandler',
        MockBookQueryHandler
    )

    # Act
    await queries_books_controller(event_book_detail)

    # Assert
    book_read_model_mock.get_book.assert_awaited_once_with("Test Book")  # Ensure the correct book was queried
    template_service_mock.render_template.assert_called_once()

    # Get the actual call arguments to compare their values
    actual_call = template_service_mock.render_template.call_args
    actual_args, actual_kwargs = actual_call

    # Extract the context from the positional arguments (since the first argument is the template name)
    actual_context = actual_args[1] if len(actual_args) > 1 else actual_kwargs.get('context')

    # Extract book from the context
    actual_book = actual_context['book']

    # Compare attributes instead of the objects themselves
    assert actual_book["title"] == "Test Book"
    assert actual_book["author"] == "Test Author"
    assert actual_book["published_date"] == "2024-01-01"
    assert actual_book["isbn"] == "1234567890"
    assert actual_book["stock_quantity"] == "10"

    # Assert that the template was called with the expected context
    expected_context = {
        "book": book_read_model_mock.get_book.return_value,
        "csrf_token": "dummy_csrf_token",
    }
    template_service_mock.render_template.assert_called_once_with(
        'book_detail.html', expected_context
    )


@pytest.mark.asyncio
async def test_edit_book(event_edit_book, monkeypatch):
    # Arrange
    form_service_mock = AsyncMock()
    form_mock = AsyncMock()
    form_mock.fields = {
        "title": MagicMock(value="Test Book"),
        "author": MagicMock(value="Test Author"),
        "published_date": MagicMock(value="2024-01-01"),
        "isbn": MagicMock(value="1234567890"),
        "stock_quantity": MagicMock(value=10),
    }
    form_service_mock.create_form.return_value = form_mock
    form_service_mock.validate_form.return_value = (True, {})

    template_service_mock = Mock()  # Mocking template service to be synchronous
    template_service_mock.render_template.return_value = "Rendered Content"

    orm_service_mock = AsyncMock()
    # Mocking a book that already exists
    orm_service_mock.get.return_value = Book(
        title="Test Book",
        author="Test Author",
        published_date=date(2024, 1, 1),
        isbn="1234567890",
        stock_quantity=10
    )
    redis_service_mock = None

    # Mock the query handler and its method
    query_handler_mock = AsyncMock()
    query_handler_mock.get_book_by_title.return_value = orm_service_mock.get.return_value

    # Use monkeypatch to replace dependencies in the DI container
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(side_effect=[form_service_mock, template_service_mock, orm_service_mock, redis_service_mock]))

    # Use monkeypatch to replace BookQueryHandler with our mocked query_handler
    monkeypatch.setattr('demo_app.controllers.queries_books_controller.BookQueryHandler', lambda *args, **kwargs: query_handler_mock)

    # Act
    await queries_books_controller(event_edit_book)

    # Assert
    query_handler_mock.get_book_by_title.assert_awaited_once_with("Test Book")  # Ensure the correct book was queried
    form_service_mock.create_form.assert_awaited_once_with(BookForm, data={
        "title": "Test Book",
        "author": "Test Author",
        "published_date": "2024-01-01",
        "isbn": "1234567890",
        "stock_quantity": 10,
    })  # Verify that the form was created with the correct book data
    template_service_mock.render_template.assert_called_once_with(
        'book_edit.html', {
            "form": form_mock,
            "errors": {},
            "csrf_token": "dummy_csrf_token"
        }
    )  # Ensure that the correct template was rendered with the right context


@pytest.mark.asyncio
async def test_edit_book_with_redis(event_edit_book, monkeypatch):
    # Arrange
    form_service_mock = AsyncMock()
    form_mock = AsyncMock()
    form_mock.fields = {
        "title": MagicMock(value="Test Book"),
        "author": MagicMock(value="Test Author"),
        "published_date": MagicMock(value="2024-01-01"),
        "isbn": MagicMock(value="1234567890"),
        "stock_quantity": MagicMock(value="10"),
    }
    form_service_mock.create_form.return_value = form_mock
    form_service_mock.validate_form.return_value = (True, {})

    template_service_mock = Mock()  # Mocking template service to be synchronous
    template_service_mock.render_template.return_value = "Rendered Content"
    orm_service_mock = AsyncMock()
    redis_service_mock = AsyncMock()

    # Mock Redis interactions in BookReadModel
    book_read_model_mock = AsyncMock()
    book_read_model_mock.get_book.return_value = {
        "title": "Test Book",
        "author": "Test Author",
        "published_date": "2024-01-01",
        "isbn": "1234567890",
        "stock_quantity": "10"
    }

    # Mock BookQueryHandler to include the mocked BookReadModel
    class MockBookQueryHandler:
        def __init__(self, *args, **kwargs):
            self.book_read_model = book_read_model_mock

        async def get_book_by_title(self, title: str):
            return await self.book_read_model.get_book(title)

    # Use monkeypatch to replace dependencies in the DI container
    monkeypatch.setattr(
        'demo_app.di_setup.di_container.get',
        AsyncMock(side_effect=[form_service_mock, template_service_mock, orm_service_mock, redis_service_mock])
    )

    # Use monkeypatch to replace BookQueryHandler with our mocked handler class
    monkeypatch.setattr(
        'demo_app.controllers.queries_books_controller.BookQueryHandler',
        MockBookQueryHandler
    )

    # Act
    await queries_books_controller(event_edit_book)

    # Assert
    book_read_model_mock.get_book.assert_awaited_once_with("Test Book")  # Ensure the correct book was queried
    form_service_mock.create_form.assert_awaited_once_with(BookForm, data={
        "title": "Test Book",
        "author": "Test Author",
        "published_date": "2024-01-01",
        "isbn": "1234567890",
        "stock_quantity": "10",
    })  # Verify that the form was created with the correct book data
    template_service_mock.render_template.assert_called_once_with(
        'book_edit.html', {
            "form": form_mock,
            "errors": {},
            "csrf_token": "dummy_csrf_token"
        }
    )  # Ensure that the correct template was rendered with the right context

