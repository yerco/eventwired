import pytest
from unittest.mock import AsyncMock, Mock, ANY

from src.event_bus import Event

from demo_app.controllers.login_controller import login_controller
from demo_app.di_setup import di_container


@pytest.mark.asyncio
async def test_login_controller_post_success_hybrid_using_real_orm(monkeypatch):
    # Initialize the real ORMService
    orm_service = await di_container.get('ORMService')
    await orm_service.init()  # This ensures that the engine and adapter are set up

    # Mock the form service
    mock_form_service = AsyncMock()

    # Create a mock form and simulate its behavior
    mock_form = AsyncMock()
    mock_form.fields = {
        'username': AsyncMock(value='validuser'),
        'password': AsyncMock(value='validpassword')
    }
    mock_form_service.create_form.return_value = mock_form  # Simulate form creation
    mock_form_service.validate_form.return_value = (True, {})  # Simulate form validation

    mock_session_service = AsyncMock()
    mock_auth_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Mock the TemplateService to return proper HTML content
    mock_template_service = AsyncMock()
    mock_template_service.render_template.return_value = "Login successful!"

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

    # Simulate an event with a mock request and no session initially
    mock_request = Mock(method="POST")
    mock_request.form = AsyncMock(return_value={
        'username': 'validuser',
        'password': 'validpassword'
    })

    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': Mock(),
        'session': None
    })

    # Call the controller with the POST request
    await login_controller(event)

    # Assert the response
    response = event.data['response']
    assert response.status_code == 200
    assert "Login successful!" in await response.content  # Await the content since it's now an actual string
    assert response.content_type == 'text/html'

    # Check that the form service was called correctly
    data = {'username': 'validuser', 'password': 'validpassword'}
    mock_form_service.create_form.assert_called_once_with(ANY, data=data)

    # Check that the AuthenticationService was called with the correct credentials
    mock_auth_service.authenticate_user.assert_called_once_with(ANY, 'validuser', 'validpassword')

    # Assert that a session was saved after login
    mock_session_service.save_session.assert_called_once()  # Make sure session was saved

    # Check that the EventBus published the login success event
    mock_event_bus.publish.assert_called_once()
    published_event = mock_event_bus.publish.call_args[0][0]

    # Ensure the user ID is correctly set
    assert published_event.name == 'user.login.success'
    assert published_event.data == {'user_id': 1}

    # Ensure a session was created and contains the correct user ID
    assert event.data['session'] is not None
    assert 'user_id' in event.data['session'].data
    assert event.data['session'].data['user_id'] == 1
