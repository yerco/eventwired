import pytest
import re

from unittest.mock import AsyncMock, patch, MagicMock
from src.event_bus import Event
from src.services.config_service import ConfigService
from src.services.orm.orm_service import ORMService
from src.services.security.authentication_service import AuthenticationService
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData, Column, Integer, String

# Use a separate MetaData object for testing
test_metadata = MetaData()
_TestBase = declarative_base(metadata=test_metadata)

class User(_TestBase):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)


@pytest.fixture(scope="function", autouse=True)
def reset_metadata():
    yield
    test_metadata.clear()  # Clears the metadata after each test


@pytest.fixture
def orm_service():
    return AsyncMock(spec=ORMService)


# Fixture to create a mocked ConfigService that can return expected configuration values
@pytest.fixture
def config_service():
    mock_config_service = MagicMock(spec=ConfigService)

    # Explicitly define the behavior of the `get` method
    def get_side_effect(key, default=None):
        config_map = {
            'TEMPLATE_ENGINE': 'JinjaAdapter',
            'TEMPLATE_DIR': 'templates'
        }
        return config_map.get(key, default)

    mock_config_service.get.side_effect = get_side_effect
    return mock_config_service


@pytest.fixture
def auth_service(orm_service, config_service):
    return AuthenticationService(orm_service=orm_service, config_service=config_service)


@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service):
    # Mock user with password
    mock_user = User(username="validuser", password="hashed_password")
    auth_service.orm_service.get_by_column.return_value = mock_user
    auth_service.password_service.check_password = MagicMock(return_value=True)

    # Test the authentication of a valid user
    result = await auth_service.authenticate_user(User, "validuser", "validpassword")
    assert result == mock_user


@pytest.mark.asyncio
async def test_authenticate_user_failure(auth_service):
    # Mock ORM to return None (user not found)
    auth_service.orm_service.get_by_column.return_value = None

    # Test authentication of a non-existing user
    result = await auth_service.authenticate_user(User, "nonexistentuser", "password")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password():
    # Arrange
    # Create a mock ORMService
    mock_orm_service = AsyncMock()
    # Simulate ORMService's get_by_column to return a User instance
    mock_user = MagicMock()
    mock_user.username = 'validuser'
    mock_user.password = 'hashed_correctpassword'  # This should match the hashed value
    mock_orm_service.get_by_column.return_value = mock_user

    # Create a mock PasswordService
    mock_password_service = MagicMock()
    # Simulate PasswordService's check_password method to return False for a wrong password
    mock_password_service.check_password.return_value = False

    # Create a mock ConfigService
    mock_config_service = MagicMock()

    # Create an instance of AuthenticationService with mocked dependencies
    auth_service = AuthenticationService(
        orm_service=mock_orm_service,
        config_service=mock_config_service
    )
    # Replace the password_service in auth_service with the mock
    auth_service.password_service = mock_password_service

    result = await auth_service.authenticate_user(User, "validuser", "wrongpassword")

    assert result is None

    # Verify that get_by_column was called with the correct arguments
    mock_orm_service.get_by_column.assert_called_once_with(User, column="username", value="validuser")
    # Verify that check_password was called with the correct arguments
    mock_password_service.check_password.assert_called_once_with("wrongpassword", mock_user.password)


@pytest.mark.asyncio
async def test_send_unauthorized_custom_template():
    # Mock the dependencies: TemplateService, ConfigService, and ORMService
    mock_template_service = MagicMock()
    mock_config_service = MagicMock()
    mock_orm_service = AsyncMock()

    # Simulate the render_template method in TemplateService to return a mocked HTML string
    mock_template_service.render_template.return_value = "<html><body>Unauthorized</body></html>"

    # Create an instance of AuthenticationService with mocked dependencies
    auth_service = AuthenticationService(
        orm_service=mock_orm_service,
        config_service=mock_config_service
    )
    # Replace the template_service with the mock
    auth_service.template_service = mock_template_service

    # Create a mock event with a mock send function
    mock_send = AsyncMock()
    event = Event(name='http.request.received', data={'send': mock_send})

    await auth_service.send_unauthorized(event)

    # Assert
    # Verify that the template was rendered with the expected context
    mock_template_service.render_template.assert_called_once_with(
        'unauthorized.html',
        {'message': 'Unauthorized: Please log in to access this page.'}
    )

    # Extract the arguments sent to `mock_send`
    start_response_call_args = mock_send.call_args_list[0][0][0]
    body_response_call_args = mock_send.call_args_list[1][0][0]

    # Expected headers (ignore order)
    expected_headers = [
        (b'content-type', b'text/html'),
        (b'Cache-Control', b'no-store, no-cache, must-revalidate, max-age=0'),
        (b'Content-Security-Policy', b"default-src 'self'"),
        (b'X-Content-Type-Options', b'nosniff'),
        (b'X-Frame-Options', b'DENY')
    ]

    # Verify the status and type for the start response
    assert start_response_call_args['type'] == 'http.response.start'
    assert start_response_call_args['status'] == 401

    # Check that each expected header is present in the response (order does not matter)
    actual_headers = start_response_call_args['headers']
    for header in expected_headers:
        assert header in actual_headers

    # Verify the body response
    assert body_response_call_args['type'] == 'http.response.body'
    assert body_response_call_args['body'] == b"<html><body>Unauthorized</body></html>"


@pytest.mark.asyncio
async def test_send_unauthorized_default_template():
    # Arrange
    mock_config_service = MagicMock()
    mock_orm_service = AsyncMock()

    mock_template_service = MagicMock()
    mock_template_service.render_template.return_value = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Unauthorized Access</title>
            <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body>
            <h1>Unauthorized Access</h1>
            <p>You do not have permission to view this page. Please log in to access it.</p>
            <div>
                <a href="/login">Login</a> | <a href="/register">Register</a>
            </div>
        </body>
        </html>
    """.strip()

    auth_service = AuthenticationService(
        orm_service=mock_orm_service,
        config_service=mock_config_service
    )
    auth_service.template_service = mock_template_service

    mock_send = AsyncMock()
    event = Event(name='http.request.received', data={'send': mock_send})

    await auth_service.send_unauthorized(event)

    start_response_call_args = mock_send.call_args_list[0][0][0]
    body_response_call_args = mock_send.call_args_list[1][0][0]

    expected_body_content = mock_template_service.render_template.return_value.strip()

    # Normalize and compare
    actual_body = body_response_call_args['body'].decode().strip()
    assert normalize_html(body_response_call_args['body'].decode()) == normalize_html(expected_body_content)

# Normalize function to remove newlines and multiple spaces
def normalize_html(html_content: str) -> str:
    return re.sub(r'\s+', ' ', html_content.strip())
