import pytest
import os
from unittest.mock import AsyncMock, Mock, ANY

from demo_app.forms.login_form import LoginForm
from src.core.request import Request
from src.event_bus import Event

from demo_app.controllers.login_controller import login_controller
from demo_app.models.user import User
from demo_app.di_setup import di_container


@pytest.mark.asyncio
async def test_login_controller_get_integration():
    # Simulate an actual HTTP GET request for the login page
    event = Event(name='http.request.received', data={
        'request': Mock(method="GET"),
        'send': Mock(),
        'csrf_token': 'test_token'
    })

    # Call the controller without needing to mock every service
    await login_controller(event)

    # Assert the response
    response = event.data['response']
    assert response.status_code == 200
    assert "Login" in response.content
    assert response.content_type == 'text/html'


@pytest.mark.asyncio
async def test_login_controller_post_success_full(monkeypatch):
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')

    # Mock the config_service.get method to return a test-specific database path
    def mock_get(key, default=None):
        if key == 'DATABASE_URL':
            return f'sqlite+aiosqlite:///test_db.db'
        return default

    # Monkeypatch the config_service.get method
    orm_service = await di_container.get('ORMService')
    monkeypatch.setattr(orm_service.config_service, 'get', mock_get)

    # Initialize the ORM service with a specific database path
    await orm_service.init(db_path="custom_test.db")
    await orm_service.create_tables()

    password_service = await di_container.get('PasswordService')
    hashed_password = password_service.hash_password('validpassword')

    # Ensure the user exists in the database with a hashed password
    await orm_service.create(User, username='validuser', password=hashed_password)

    async def mock_receive():
        return {
            'body': b'username=validuser&password=validpassword',
            'more_body': False
        }

    # Create a Request object simulating a real POST request
    request = Request(scope={'method': 'POST'}, receive=mock_receive)

    # Mock the TemplateService to avoid using real templates
    mock_template_service = AsyncMock()
    mock_template_service.render_template.return_value = "Login successful"

    # Mock the form service
    mock_form_service = AsyncMock()

    # Create a mock form and simulate its behavior
    mock_form = AsyncMock()
    mock_form.fields = {
        'username': AsyncMock(value='validuser'),
        'password': AsyncMock(value='validpassword')
    }
    mock_form_service.create_form.return_value = mock_form  # Simulate form creation

    # Mock `validate_form` to return two values: (True, {})
    mock_form_service.validate_form.return_value = (True, {})  # Simulate successful validation

    # Mock other services
    mock_session_service = AsyncMock()
    mock_auth_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Simulate a valid user with an explicit user ID
    mock_user = AsyncMock()
    mock_user.id = 1  # Set the user ID to 1
    mock_user.username = 'validuser'
    mock_auth_service.authenticate_user.return_value = mock_user  # Return the mock user

    # Inject the services through DI container
    async def mock_get(service_name):
        services = {
            'FormService': mock_form_service,
            'ORMService': orm_service,  # Use the real ORMService
            'SessionService': mock_session_service,  # Mocked session service
            'AuthenticationService': mock_auth_service,
            'EventBus': mock_event_bus,
            'TemplateService': mock_template_service,
        }
        return services.get(service_name)

    monkeypatch.setattr(di_container, 'get', mock_get)

    # Prepare the event with real DI container and other dependencies
    event = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock(),  # Mock the send function for the ASGI response
        'session': None
    })

    # Call the login_controller with the real container
    await login_controller(event)

    # Extract and assert the response from the event
    response = event.data.get('response')

    # Ensure the response is successful
    assert response is not None
    assert response.status_code == 200
    assert "Login successful" in await response.content
    assert response.content_type == 'text/html'

    # Clean up
    os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_controller_invalid_method_integration():
    # Simulate a request with an unsupported method (e.g., PUT)
    mock_request = Mock(method="PUT")

    # Simulate an event with a mock request
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': Mock(),
        'session': None
    })

    # Call the controller with the invalid method
    await login_controller(event)

    # Assert the response
    response = event.data['response']
    assert response.status_code == 405  # Method Not Allowed
    assert "Method Not Allowed" in response.content
    assert response.content_type == 'text/plain'
