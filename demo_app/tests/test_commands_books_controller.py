import pytest
from unittest.mock import AsyncMock, patch, MagicMock, Mock
from datetime import date

from src.core.event_bus import Event

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

        # Mock RedisService for read model updates
        redis_service_mock = AsyncMock()

        # Register all mocks to the DI container
        mock_get.side_effect = [
            form_service_mock, template_service_mock, orm_service_mock, redis_service_mock
        ]

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

        # Ensure the read model is updated if Redis is enabled
        redis_service_mock.set_session.assert_called_once_with(
            "book:Test Book",
            {
                "id": str(created_book_mock.id),
                "title": "Test Book",
                "author": "Test Author",
                "published_date": "2024-01-01",
                "isbn": "9876543210",
                "stock_quantity": "10"
            }
        )


@pytest.mark.asyncio
async def test_add_book_duplicate_title(event_add_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
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

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `get` method to simulate an existing book (duplicate found)
        existing_book_mock = Book(
            title="Test Book",
            author="Test Author",
            published_date=date(2024, 1, 1),
            isbn="1234567890",
            stock_quantity=10
        )
        orm_service_mock.get.return_value = existing_book_mock

        # Adding a mock for RedisService (even if it's not used in this case)
        redis_service_mock = None

        # Add the mocks to the side_effect list in the correct order
        mock_get.side_effect = [form_service_mock, template_service_mock, orm_service_mock, redis_service_mock]

        # Call the controller
        await commands_books_controller(event_add_book)

        # Assertions to verify the correct handling of a duplicate book
        orm_service_mock.create.assert_not_called()
        template_service_mock.render_template.assert_called_once_with(
            'book_add.html',
            {
                "form": form_mock,
                "errors": {"general": ["A book with this title and author already exists."]},
                "csrf_token": "dummy_csrf_token"
            }
        )


async def test_add_book_unexpected_error(event_add_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
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

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `get` method to return None for both title and ISBN to simulate no duplicates
        orm_service_mock.get.return_value = None

        # Mock ORM's `create` method to raise an exception
        orm_service_mock.create.side_effect = Exception("Unexpected Error")

        redis_service_mock = None

        mock_get.side_effect = [
            form_service_mock,   # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,  # ORMService
            redis_service_mock  # RedisService (None in this case)
        ]

        # Call the controller
        await commands_books_controller(event_add_book)

        # Assertions to verify correct error handling
        template_service_mock.render_template.assert_called_once_with(
            'book_add.html',
            {
                "form": form_mock,
                "errors": {"general": ["An unexpected error occurred. Please try again later"]},
                "csrf_token": "dummy_csrf_token"
            }
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
            "published_date": MagicMock(value="2024-01-01"),
            "isbn": MagicMock(value="0987654321"),
            "stock_quantity": MagicMock(value=15),
        }
        form_service_mock.create_form.return_value = form_mock
        form_service_mock.validate_form.return_value = (True, {})

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `update` method to simulate successful update
        orm_service_mock.update.return_value = Book(
            title="Updated Test Book",
            author="Updated Author",
            published_date=date(2024, 1, 1),
            isbn="0987654321",
            stock_quantity=15
        )

        redis_service_mock = None

        mock_get.side_effect = [
            form_service_mock,  # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,  # ORMService
            redis_service_mock  # RedisService
        ]

        # Call the controller
        await commands_books_controller(event_update_book)

        # Assertions to verify correct behavior
        orm_service_mock.update.assert_called_once_with(
            Book,
            lookup_value="Test Book",
            lookup_column="title",
            title="Updated Test Book",
            author="Updated Author",
            published_date=date(2024, 1, 1),
            isbn="0987654321",
            stock_quantity=15,
            return_instance=True
        )
        template_service_mock.render_template.assert_called_once_with(
            'book_success.html', {"message": "Book titled 'Test Book' updated successfully."}
        )


@pytest.mark.asyncio
async def test_update_book_invalid_form(event_update_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        form_mock = AsyncMock()
        # Use actual string values for form fields to avoid the TypeError
        form_mock.fields = {
            "title": MagicMock(value="Updated Test Book"),
            "author": MagicMock(value="Updated Author"),
            "published_date": MagicMock(value="2024-01-01"),  # Use string format to match the expected input type
            "isbn": MagicMock(value="0987654321"),
            "stock_quantity": MagicMock(value="15"),
        }
        form_service_mock.create_form.return_value = form_mock
        form_service_mock.validate_form.return_value = (False, {"title": ["This field is required"]})

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()
        redis_service_mock = None

        mock_get.side_effect = [
            form_service_mock,
            template_service_mock,
            orm_service_mock,
            redis_service_mock
        ]

        # Call the controller
        await commands_books_controller(event_update_book)

        # Assertions to verify correct behavior when form is invalid
        template_service_mock.render_template.assert_called_once_with(
            'book_edit.html',
            {
                "form": form_mock,
                "errors": {"title": ["This field is required"]},
                "csrf_token": "dummy_csrf_token"
            }
        )


@pytest.mark.asyncio
async def test_update_book_not_found(event_update_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        form_mock = AsyncMock()
        form_mock.fields = {
            "title": MagicMock(value="Updated Test Book"),
            "author": MagicMock(value="Updated Author"),
            "published_date": MagicMock(value="2024-01-01"),
            "isbn": MagicMock(value="0987654321"),
            "stock_quantity": MagicMock(value="15"),
        }
        form_service_mock.create_form.return_value = form_mock
        form_service_mock.validate_form.return_value = (True, {})

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `update` method to simulate book not found
        orm_service_mock.update.return_value = False

        redis_service_mock = None

        # Setting up the side effect of `get` to simulate DI container behavior
        mock_get.side_effect = [
            form_service_mock,  # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,  # ORMService
            redis_service_mock  # RedisService
        ]

        # Mock `send_error` and `send_html` on the controller instance used in the test
        with patch("demo_app.controllers.commands_books_controller.HTTPController") as MockHTTPController:
            mock_controller_instance = MockHTTPController.return_value
            mock_controller_instance.send_error = AsyncMock()
            mock_controller_instance.send_html = AsyncMock()

            # Call the controller
            await commands_books_controller(event_update_book)

            # Assertions to verify correct error handling when book is not found
            mock_controller_instance.send_error.assert_awaited_once_with(404, "Book not found")


@pytest.mark.asyncio
async def test_update_book_unexpected_error(event_update_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        form_mock = AsyncMock()
        form_mock.fields = {
            "title": MagicMock(value="Updated Test Book"),
            "author": MagicMock(value="Updated Author"),
            "published_date": MagicMock(value="2024-01-01"),
            "isbn": MagicMock(value="1234567890"),
            "stock_quantity": MagicMock(value="15"),
        }
        form_service_mock.create_form.return_value = form_mock
        form_service_mock.validate_form.return_value = (True, {})

        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()

        # Mock ORM's `update` method to raise an unexpected error
        orm_service_mock.update.side_effect = Exception("Unexpected Error")

        redis_service_mock = None

        mock_get.side_effect = [
            form_service_mock,  # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,  # ORMService
            redis_service_mock  # RedisService
        ]

        # Mock `send_error` and `send_html` on the controller instance used in the test
        with patch("demo_app.controllers.commands_books_controller.HTTPController") as MockHTTPController:
            mock_controller_instance = MockHTTPController.return_value
            mock_controller_instance.send_error = AsyncMock()
            mock_controller_instance.send_html = AsyncMock()

            # Call the controller
            await commands_books_controller(event_update_book)

            # Assertions to verify correct error handling when an unexpected error occurs
            mock_controller_instance.send_error.assert_awaited_once_with(
                500, "Error updating book: Unexpected Error"
            )


@pytest.mark.asyncio
async def test_delete_book_success(event_delete_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        template_service_mock = MagicMock()
        template_service_mock.render_template.return_value = "Book deleted successfully."
        orm_service_mock = AsyncMock()
        orm_service_mock.delete.return_value = True  # Mock delete operation

        redis_service_mock = None

        # Set up the side effect for DI container
        mock_get.side_effect = [
            form_service_mock,  # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,  # ORMService
            redis_service_mock,
        ]

        # Mock `send_html` on the controller instance used in the test
        with patch("demo_app.controllers.commands_books_controller.HTTPController") as MockHTTPController:
            mock_controller_instance = MockHTTPController.return_value
            mock_controller_instance.send_html = AsyncMock()

            # Call the controller
            await commands_books_controller(event_delete_book)

            # Assertions to verify correct behavior
            orm_service_mock.delete.assert_called_once_with(Book, lookup_value="Test Book", lookup_column="title")
            template_service_mock.render_template.assert_called_once_with(
                'book_success.html', {"message": "Book titled 'Test Book' deleted successfully."}
            )
            mock_controller_instance.send_html.assert_awaited_once_with("Book deleted successfully.")


@pytest.mark.asyncio
async def test_delete_book_not_found(event_delete_book):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        template_service_mock = Mock()
        # Mock `render_template` to return a rendered HTML string
        template_service_mock.render_template.return_value = "<html><body>Book not found</body></html>"

        orm_service_mock = AsyncMock()
        # Mock ORM's `delete` method to return False, simulating book not found
        orm_service_mock.delete.return_value = False
        redis_service_mock = None

        # Set up the side effect for DI container
        mock_get.side_effect = [
            form_service_mock,  # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,  # ORMService
            redis_service_mock,
        ]

        # Mock `send_error` and `send_html` on the controller instance used in the test
        with patch("demo_app.controllers.commands_books_controller.HTTPController") as MockHTTPController:
            mock_controller_instance = MockHTTPController.return_value
            mock_controller_instance.send_error = AsyncMock()
            mock_controller_instance.send_html = AsyncMock()

            # Call the controller
            await commands_books_controller(event_delete_book)

            # Assertions to verify correct error handling when book is not found
            try:
                mock_controller_instance.send_error.assert_awaited_once_with(404, "Book not found")
                print("send_error was called with 404 as expected.")
            except AssertionError:
                print("send_error was NOT called as expected.")
                print(f"Mock calls made: {mock_controller_instance.send_error.mock_calls}")

            mock_controller_instance.send_error.assert_awaited_once_with(404, "Book not found")


@pytest.fixture
def event_delete_book_wrong_method():
    request_mock = AsyncMock()
    request_mock.method = "POST"
    request_mock.path = "/books/Test%20Book/delete"
    request_mock.form.return_value = {
        "_method": ["PATCH"],  # Use an incorrect method
    }
    mock_send = AsyncMock()
    event_data = {
        "request": request_mock,
        "csrf_token": "dummy_csrf_token",
        "send": mock_send,
    }
    return Event(name="http.request.received", data=event_data)


@pytest.mark.asyncio
async def test_delete_book_method_not_allowed(event_delete_book_wrong_method):
    with patch("demo_app.di_setup.di_container.get") as mock_get:
        # Mock dependencies
        form_service_mock = AsyncMock()
        template_service_mock = MagicMock()
        orm_service_mock = AsyncMock()
        redis_service_mock = None  # Assume RedisService might not be available

        # Set up the side effect for DI container
        mock_get.side_effect = [
            form_service_mock,      # FormService
            template_service_mock,  # TemplateService
            orm_service_mock,       # ORMService
            redis_service_mock      # RedisService
        ]

        # Mock `send_error` on the controller instance used in the test
        with patch("demo_app.controllers.commands_books_controller.HTTPController") as MockHTTPController:
            mock_controller_instance = MockHTTPController.return_value
            mock_controller_instance.send_error = AsyncMock()

            # Call the controller
            await commands_books_controller(event_delete_book_wrong_method)

            # Assertions to verify correct handling of wrong method override
            mock_controller_instance.send_error.assert_awaited_once_with(405, "Method Not Allowed")
