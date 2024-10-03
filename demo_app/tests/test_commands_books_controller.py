import pytest
from unittest.mock import AsyncMock, patch, MagicMock, ANY, Mock
from datetime import date

from src.event_bus import Event

from demo_app.controllers.commands_books_controller import commands_books_controller
from demo_app.models.book import Book


# Fixtures to simulate the event and required services
@pytest.fixture
def event_add_book():
    request_mock = AsyncMock()
    request_mock.method = "POST"
    request_mock.path = "/books/action/add"
    request_mock.form.return_value = {
        "title": ["Test Book"],
        "author": ["Test Author"],
        "published_date": ["2024-01-01"],  # Correct date format
        "isbn": ["1234567890"],
        "stock_quantity": ["10"],  # Correct integer as a string
    }
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.fixture
def event_update_book():
    request_mock = AsyncMock()
    request_mock.method = "POST"
    request_mock.path = "/books/Test%20Book/edit"
    request_mock.form.return_value = {
        "title": ["Updated Test Book"],
        "author": ["Updated Author"],
        "published_date": ["2024-01-01"],  # Correct date format
        "isbn": ["0987654321"],
        "stock_quantity": ["15"],  # Correct integer as a string
        "_method": ["PATCH"],
    }
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.fixture
def event_delete_book():
    request_mock = AsyncMock()
    request_mock.method = "POST"
    request_mock.path = "/books/Test%20Book/delete"
    request_mock.form.return_value = {
        "_method": ["DELETE"],
    }
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.mark.asyncio
async def test_add_book_success(event_add_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        form_mock = AsyncMock()
        form_mock.fields = {
            "title": MagicMock(value="Test Book"),
            "author": MagicMock(value="Test Author"),
            "published_date": MagicMock(value="2024-01-01"),  # Use string format here
            "isbn": MagicMock(value="9876543210"),  # Unique ISBN to avoid conflict
            "stock_quantity": MagicMock(value="10"),  # Use string to simulate form submission
        }
        form_service_mock.create_form.return_value = form_mock
        form_service_mock.validate_form.return_value = (True, {})

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `get` method to return None, simulating no existing book (no duplicate found)
        orm_service_mock.get.return_value = None

        # Mock ORM's `create` method to return a Book instance
        created_book_mock = Book(
            title="Test Book",
            author="Test Author",
            published_date=date(2024, 1, 1),
            isbn="9876543210",
            stock_quantity=10
        )
        orm_service_mock.create.return_value = created_book_mock

        mock_get.side_effect = [form_service_mock, template_service_mock, orm_service_mock]

        # Call the controller
        await commands_books_controller(event_add_book)

        # Assertions to verify correct behavior
        orm_service_mock.create.assert_called_once_with(
            Book,
            title="Test Book",
            author="Test Author",
            published_date=date(2024, 1, 1),
            isbn="9876543210",
            stock_quantity=10
        )
        template_service_mock.render_template.assert_called_once_with(
            'book_success.html', {"message": "Book 'Test Book' by Test Author added successfully."}
        )


@pytest.mark.asyncio
async def test_update_book_success(event_update_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        form_mock = AsyncMock()
        form_mock.fields = {
            "title": MagicMock(value="Updated Test Book"),
            "author": MagicMock(value="Updated Author"),
            "published_date": MagicMock(value="2024-01-01"),  # Use string format to match the expected input type
            "isbn": MagicMock(value="0987654321"),
            "stock_quantity": MagicMock(value=15),
        }
        form_service_mock.create_form.return_value = form_mock
        form_service_mock.validate_form.return_value = (True, {})

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `get` and `update` methods
        existing_book = Book(
            title="Test Book",
            author="Test Author",
            published_date=date(2024, 1, 1),
            isbn="1234567890",
            stock_quantity=10
        )
        orm_service_mock.get.return_value = existing_book
        orm_service_mock.update.return_value = existing_book

        mock_get.side_effect = [form_service_mock, template_service_mock, orm_service_mock]

        # Call the controller
        await commands_books_controller(event_update_book)

        # Assertions to verify correct behavior
        orm_service_mock.update.assert_called_once_with(
            Book,
            lookup_value="Test Book",
            lookup_column="title",
            title="Updated Test Book",
            author="Updated Author",
            published_date=date(2024, 1, 1),  # Convert the string to a date object as needed in the ORM service
            isbn="0987654321",
            stock_quantity=15
        )
        template_service_mock.render_template.assert_called_once_with(
            'book_success.html', {"message": "Book titled 'Test Book' updated successfully."}
        )


@pytest.mark.asyncio
async def test_delete_book_success(event_delete_book):
    # Arrange
    orm_service_mock = AsyncMock()
    orm_service_mock.delete.return_value = True  # Mock delete operation
    form_service_mock = AsyncMock()
    template_service_mock = Mock()
    template_service_mock.render_template.return_value = "Book deleted successfully."

    # Inject mocked dependencies
    with patch('demo_app.di_setup.di_container.get', side_effect=[form_service_mock, template_service_mock, orm_service_mock]):
        # Act
        await commands_books_controller(event_delete_book)

        # Assert
        orm_service_mock.delete.assert_called_once_with(Book, lookup_value="Test Book", lookup_column="title")
        template_service_mock.render_template.assert_called_once_with(
            'book_success.html', {"message": "Book titled 'Test Book' deleted successfully."}
        )
