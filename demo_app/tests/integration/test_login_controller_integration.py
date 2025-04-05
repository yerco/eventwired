import pytest
import os
from unittest.mock import AsyncMock, Mock

from demo_app.di_setup import setup_container
from src.core.context_manager import set_container
from src.core.dicontainer import DIContainer
from src.core.request import Request
from src.core.event_bus import Event

from demo_app.controllers.login_controller import login_controller
from demo_app.models.user import User


@pytest.mark.asyncio
async def test_login_controller_get_integration():
    container = DIContainer()
    await setup_container(container)
    set_container(container)
    # Simulate an actual HTTP GET request for the login page
    event = Event(name='http.request.received', data={
        'request': Mock(method="GET"),
        'send': Mock(),
        'csrf_token': 'test_token'
    })

    # Call the controller without needing to mock every service
    await login_controller(event, form_service=await container.get('FormService'), template_service=await container.get('TemplateService'),
                           auth_service=await container.get('AuthenticationService'), session_service=await container.get('SessionService'))

    # Assert the response
    response = event.data['response']
    assert response.status_code == 200
    assert "Login" in response.content
    assert response.content_type == 'text/html'


# Not that 'integration' kind of test
@pytest.mark.asyncio
async def test_login_controller_post_success_full(monkeypatch):
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    test_config = {
        'BASE_DIR': base_dir,
        'TEMPLATE_DIR': os.path.join(base_dir, 'templates'),
        'CORS_ALLOWED_ORIGINS': ["http://allowed-origin.com", "http://*.example.com"],
        'CORS_ALLOWED_METHODS': ["GET", "POST", "OPTIONS"],
        'CORS_ALLOWED_HEADERS': ["Content-Type", "Authorization"],
        'CORS_ALLOW_CREDENTIALS': True,
        'DATABASE_URL': 'sqlite+aiosqlite:///test_db.db',
        'JWT_SECRET_KEY': 'test_secret_key',
    }
    container = DIContainer()
    await setup_container(container, test_config)
    set_container(container)
    template_service = await container.get('TemplateService')
    monkeypatch.setattr(template_service, 'render_template', AsyncMock(return_value="Login successful"))

    # Create a mock form and simulate its behavior
    mock_form = AsyncMock()
    mock_form.fields = {
        'username': AsyncMock(value='validuser'),
        'password': AsyncMock(value='validpassword')
    }
    form_service = await container.get('FormService')
    monkeypatch.setattr(form_service, 'create_form', AsyncMock(return_value=mock_form))
    monkeypatch.setattr(form_service, 'validate_form', AsyncMock(return_value=(True, {})))

    # Simulate a valid user with an explicit user ID
    mock_user = Mock()
    mock_user.id = 1  # Set the user ID to 1
    mock_user.is_admin = True
    mock_user.username = 'validuser'
    auth_service = await container.get('AuthenticationService')
    monkeypatch.setattr(auth_service, 'authenticate_user', AsyncMock(return_value=mock_user))

    password_service = await container.get('PasswordService')
    hashed_password = password_service.hash_password('validpassword')

    orm_service = await container.get('ORMService')
    monkeypatch.setattr(orm_service, 'create', AsyncMock())
    orm_service.create.return_value = User(username='validuser', password=hashed_password)

    async def mock_receive():
        return {
            'body': b'username=validuser&password=validpassword',
            'more_body': False
        }

    # Create a Request object simulating a real POST request
    request = Request(scope={'method': 'POST'}, receive=mock_receive)

    # Prepare the event with real DI container and other dependencies
    event = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock(),  # Mock the send function for the ASGI response
        'session': None
    })

    # Call the login_controller with the real container
    await login_controller(event, form_service=await container.get('FormService'), template_service=await container.get('TemplateService'),
                           auth_service=await container.get('AuthenticationService'), session_service=await container.get('SessionService'))

    # Extract and assert the response from the event
    response = event.data.get('response')

    # Ensure the response is successful
    assert response is not None
    assert response.status_code == 200
    assert "Welcome, validuser!" in response.content
    assert response.content_type == 'text/html'

    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_controller_invalid_method_integration():
    container = DIContainer()
    await setup_container(container)
    set_container(container)
    # Simulate a request with an unsupported method (e.g., PUT)
    mock_request = Mock(method="PUT")

    # Simulate an event with a mock request
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': Mock(),
        'session': None
    })

    # Call the controller with the invalid method
    await login_controller(event, form_service=await container.get('FormService'), template_service=await container.get('TemplateService'),
                           auth_service=await container.get('AuthenticationService'), session_service=await container.get('SessionService'))

    # Assert the response
    response = event.data['response']
    assert response.status_code == 405  # Method Not Allowed
    assert "Method Not Allowed" in response.content
    assert response.content_type == 'text/plain'
