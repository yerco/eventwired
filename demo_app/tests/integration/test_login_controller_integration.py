import pytest
import os
from unittest.mock import AsyncMock, Mock

from src.core.dicontainer import di_container, DIContainer
from src.core.request import Request
from src.core.event_bus import Event, EventBus
from src.services.form_service import FormService
from src.services.orm_service import ORMService
from src.services.security.authentication_service import AuthenticationService
from src.services.session_service import SessionService
from src.services.template_service import TemplateService
from src.services.config_service import ConfigService

from demo_app.controllers.login_controller import login_controller
from demo_app.models.user import User
from demo_app.config import config


# Special container for the test, precaution to not stomp real db
@pytest.fixture(autouse=True)
async def container():
    di_container = DIContainer()
    # Replacing the database
    config['DATABASE_URL'] = 'sqlite:///test_db.db'
    config_service = ConfigService(config)
    di_container.register_singleton_instance(config_service, 'ConfigService')
    di_container.register_singleton_class(FormService, 'FormService')
    di_container.register_singleton_class(TemplateService, 'TemplateService')
    di_container.register_singleton_class(AuthenticationService, 'AuthenticationService')
    di_container.register_singleton_class(ORMService, 'ORMService')
    di_container.register_singleton_class(SessionService, 'SessionService')
    di_container.register_singleton_class(EventBus, 'EventBus')
    yield di_container
    # cleanup
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_controller_get_integration(monkeypatch, container):
    monkeypatch.setattr('src.core.framework_app.di_container', container)

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


# Not that 'integration' kind of test
@pytest.mark.asyncio
async def test_login_controller_post_success_full(monkeypatch):
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
    mock_orm_service = AsyncMock()

    # Simulate a valid user with an explicit user ID
    mock_user = Mock()
    mock_user.id = 1  # Set the user ID to 1
    mock_user.username = 'validuser'
    mock_auth_service.authenticate_user.return_value = mock_user  # Return the mock user

    mock_password_service = AsyncMock()

    # Inject the services through DI container
    async def mock_get(service_name):
        services = {
            'FormService': mock_form_service,
            'ORMService': mock_orm_service,  # Use the real ORMService
            'SessionService': mock_session_service,  # Mocked session service
            'AuthenticationService': mock_auth_service,
            'EventBus': mock_event_bus,
            'TemplateService': mock_template_service,
            'PasswordService': mock_password_service,
        }
        return services.get(service_name)

    monkeypatch.setattr(di_container, 'get', mock_get)
    password_service = await di_container.get('PasswordService')
    hashed_password = await password_service.hash_password('validpassword')

    # Ensure the user exists in the database with a hashed password
    await mock_orm_service.create(User, username='validuser', password=hashed_password)

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
    await login_controller(event)

    # Extract and assert the response from the event
    response = event.data.get('response')

    # Ensure the response is successful
    assert response is not None
    assert response.status_code == 200
    assert "Login successful" in await response.content
    assert response.content_type == 'text/html'


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
