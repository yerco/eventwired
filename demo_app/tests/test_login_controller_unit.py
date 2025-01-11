import pytest
from unittest.mock import AsyncMock, Mock, ANY

from src.core.context_manager import set_container
from src.core.dicontainer import DIContainer
from src.core.response import Response
from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.controllers.login_controller import login_controller
from demo_app.models.user import User


@pytest.mark.asyncio
async def test_login_controller_get_one(monkeypatch):
    container = DIContainer()
    set_container(container)

    # Create mock services
    mock_template_service = Mock()  # Use Mock instead of AsyncMock
    mock_send_response = AsyncMock()
    mock_form_service = AsyncMock()
    mock_authentication_service = AsyncMock()
    mock_session_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Mock the template rendering to return HTML content
    mock_template_service.render_template.return_value = "<html>Login Page</html>"

    # Monkeypatch the DI container to return the mocked services
    async def mock_get(service_name):
        services = {
            'TemplateService': mock_template_service,
            'FormService': mock_form_service,
            'AuthenticationService': mock_authentication_service,
            'SessionService': mock_session_service,
            'EventBus': mock_event_bus,
        }
        return services[service_name]

    monkeypatch.setattr(container, 'get', mock_get)

    # Monkeypatch HTTPController's send_response to track the response flow
    monkeypatch.setattr(HTTPController, 'send_response', mock_send_response)

    # Mock request with GET method
    mock_request = AsyncMock()
    mock_request.method = "GET"
    mock_send = AsyncMock()

    # Create the event object and include the 'send' key
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': mock_send,  # Mocked send function for HTTPController
    })

    # Call the login_controller
    await login_controller(event, form_service=mock_form_service, template_service=mock_template_service,
                           auth_service=mock_authentication_service, session_service=mock_session_service,
                           event_bus=mock_event_bus)

    # Check that the template service was used to render the login form
    mock_template_service.render_template.assert_called_once_with('login.html', {
        "form": ANY,  # Bypass the memory address comparison for the form
        "errors": {},
        "csrf_token": event.data['request'].csrf_token
    })

    # Ensure the response was sent
    mock_send_response.assert_called_once()

    # Extract the response object from the call args
    response = mock_send_response.call_args[0][0]  # First positional arg is the response object

    # Check response content and status
    assert response.content_type == 'text/html'
    assert response.content == "<html>Login Page</html>"  # Now no await needed
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_controller_get_two(monkeypatch):
    container = DIContainer()
    set_container(container)

    # Create mock services
    mock_template_service = AsyncMock()
    mock_send_response = AsyncMock()
    mock_form_service = AsyncMock()
    mock_authentication_service = AsyncMock()
    mock_session_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Mock the template rendering to return HTML content
    mock_template_service.render_template.return_value = "<html>Login Page</html>"

    # Monkeypatch the DI container to return the mocked services
    async def mock_get(service_name):
        services = {
            'TemplateService': mock_template_service,
            'FormService': mock_form_service,
            'AuthenticationService': mock_authentication_service,
            'SessionService': mock_session_service,
            'EventBus': mock_event_bus,
        }
        return services[service_name]

    monkeypatch.setattr(container, 'get', mock_get)

    # Monkeypatch HTTPController's send_response to track the response flow
    monkeypatch.setattr(HTTPController, 'send_response', mock_send_response)

    # Mock request with GET method
    mock_request = Mock()
    mock_request.method = "GET"
    monkeypatch.setattr(mock_request, 'csrf_token', "test_token")  # Directly set csrf_token value
    mock_send = AsyncMock()

    # Create the event object and include the 'send' key
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': mock_send,  # Mocked send function for HTTPController
    })

    # Call the login_controller
    await login_controller(event, form_service=mock_form_service, template_service=mock_template_service,
                           auth_service=mock_authentication_service, session_service=mock_session_service,
                           event_bus=mock_event_bus)

    # Check that the template service was used to render the login form
    mock_template_service.render_template.assert_called_once_with('login.html', {
        "form": ANY,  # Bypass the memory address comparison for the form
        "errors": {},
        "csrf_token": "test_token"
    })

    # Ensure the response was sent
    mock_send_response.assert_called_once()

    # Extract the response object from the call args
    response = mock_send_response.call_args[0][0]  # First positional arg is the response object

    # Check response content and status
    assert response.content_type == 'text/html'
    content = await response.content
    assert content == "<html>Login Page</html>"  # Check if the mocked HTML is used
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_controller_post_success(monkeypatch):
    container = DIContainer()
    set_container(container)

    # Create mock services
    mock_template_service = AsyncMock()
    mock_send_response = AsyncMock()
    mock_form_service = AsyncMock()
    mock_authentication_service = AsyncMock()
    mock_session_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Mock the form service to simulate a valid form
    mock_form = AsyncMock()
    mock_form.fields = {
        'username': AsyncMock(value='validuser'),
        'password': AsyncMock(value='validpassword')
    }
    mock_form_service.create_form.return_value = mock_form
    mock_form_service.validate_form.return_value = (True, {})

    # Mock the authentication service to return a valid user
    mock_user = User(id=1, username='validuser')
    mock_authentication_service.authenticate_user.return_value = mock_user

    # Set the mock TemplateService to return proper HTML content
    mock_template_service.render_template.return_value = "Login successful! Welcome, validuser."

    # Monkeypatch the DI container to return the mocked services
    async def mock_get(service_name):
        services = {
            'TemplateService': mock_template_service,
            'FormService': mock_form_service,
            'AuthenticationService': mock_authentication_service,
            'SessionService': mock_session_service,
            'EventBus': mock_event_bus,
        }
        return services[service_name]

    monkeypatch.setattr(container, 'get', mock_get)

    # Monkeypatch HTTPController's send_response to track the response flow
    monkeypatch.setattr(HTTPController, 'send_response', mock_send_response)

    # Mock request with POST method and valid form data
    mock_request = AsyncMock()
    mock_request.method = "POST"
    mock_request.form.return_value = {
        'username': 'validuser',
        'password': 'validpassword'
    }
    mock_send = AsyncMock()

    # Create the event object and include the 'send' key
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': mock_send,  # Mocked send function for HTTPController
    })

    # Call the login_controller
    await login_controller(event, form_service=mock_form_service, template_service=mock_template_service,
                           auth_service=mock_authentication_service, session_service=mock_session_service,
                           event_bus=mock_event_bus)

    # Check that the form service was used to create and validate the form
    mock_form_service.create_form.assert_called_once_with(ANY, data={'username': 'validuser', 'password': 'validpassword'})
    mock_form_service.validate_form.assert_called_once_with(mock_form)

    # Check that the authentication service was called with the correct username and password
    mock_authentication_service.authenticate_user.assert_called_once_with(User, 'validuser', 'validpassword')

    # Check that the session service was called to save the session
    mock_session_service.save_session.assert_called_once()

    # Check that the event bus published the login success event
    mock_event_bus.publish.assert_called_once()
    published_event = mock_event_bus.publish.call_args[0][0]
    assert published_event.name == 'user.login.success'
    assert published_event.data == {'user_id': 1}

    # Ensure the response was sent
    mock_send_response.assert_called_once()

    # Extract the response object from the call args
    response = mock_send_response.call_args[0][0]  # First positional arg is the response object

    # Await the content of the response to get the actual value
    assert await response.content == "Login successful! Welcome, validuser."
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_controller_post_invalid_credentials(monkeypatch):
    container = DIContainer()
    set_container(container)

    # Create mock services
    mock_template_service = Mock()  # Use Mock instead of AsyncMock
    mock_send_response = AsyncMock()
    mock_form_service = AsyncMock()
    mock_authentication_service = AsyncMock()
    mock_session_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Mock the form service to simulate a valid form
    mock_form = AsyncMock()
    mock_form.fields = {
        'username': AsyncMock(value='invaliduser'),
        'password': AsyncMock(value='invalidpassword')
    }
    mock_form_service.create_form.return_value = mock_form
    mock_form_service.validate_form.return_value = (True, {})  # Assume form is valid

    # Mock the authentication service to return None (indicating invalid credentials)
    mock_authentication_service.authenticate_user.return_value = None

    # Mock template rendering to simulate rendering an HTML response
    mock_template_service.render_template.return_value = "<html>Invalid Credentials</html>"

    # Mock the response to return a Response object when send_response is called
    mock_response = Response(content="<html>Invalid Credentials</html>", status_code=400, content_type='text/html')
    mock_send_response.return_value = mock_response

    # Monkeypatch the DI container to return the mocked services
    async def mock_get(service_name):
        services = {
            'TemplateService': mock_template_service,
            'FormService': mock_form_service,
            'AuthenticationService': mock_authentication_service,
            'SessionService': mock_session_service,
            'EventBus': mock_event_bus,
        }
        return services[service_name]

    monkeypatch.setattr(container, 'get', mock_get)

    # Monkeypatch HTTPController's send_response to track the response flow
    monkeypatch.setattr(HTTPController, 'send_response', mock_send_response)

    # Mock request with POST method and invalid credentials
    mock_request = AsyncMock()
    mock_request.method = "POST"
    mock_request.form.return_value = {
        'username': 'invaliduser',
        'password': 'invalidpassword'
    }
    mock_send = AsyncMock()

    # Create the event object and include the 'send' key
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': mock_send  # Mocked send function for HTTPController
    })

    # Call the login_controller
    await login_controller(event, form_service=mock_form_service, template_service=mock_template_service,
                           auth_service=mock_authentication_service, session_service=mock_session_service,
                           event_bus=mock_event_bus)

    # Check that the form service was used to create and validate the form
    mock_form_service.create_form.assert_called_once_with(ANY, data={'username': 'invaliduser', 'password': 'invalidpassword'})
    mock_form_service.validate_form.assert_called_once_with(mock_form)

    # Check that the authentication service was called with the correct username and password
    mock_authentication_service.authenticate_user.assert_called_once_with(User, 'invaliduser', 'invalidpassword')

    # Check that the event bus published the login failure event
    mock_event_bus.publish.assert_called_once()
    published_event = mock_event_bus.publish.call_args[0][0]
    assert published_event.name == 'user.login.failure'
    assert published_event.data == {'username': 'invaliduser'}

    # Ensure the response was sent
    mock_send_response.assert_called_once()

    # Extract the response object from the call args
    response = mock_send_response.call_args[0][0]  # First positional arg is the response object

    # Since template rendering is synchronous, no need to await
    content = response.content

    # Check response content and status
    assert response.content_type == 'text/html'
    assert content == "<html>Invalid Credentials</html>"  # Check the mocked content
    assert response.status_code == 401  # Should return a 400 status for invalid credentials


@pytest.mark.asyncio
async def test_login_controller_post_invalid_form(monkeypatch):
    container = DIContainer()
    set_container(container)

    # Create mock services
    mock_template_service = Mock()  # Use Mock instead of AsyncMock
    mock_send_response = AsyncMock()
    mock_form_service = AsyncMock()
    mock_authentication_service = AsyncMock()
    mock_session_service = AsyncMock()
    mock_event_bus = AsyncMock()

    # Mock the form service to simulate an invalid form
    mock_form = AsyncMock()
    mock_form.fields = {
        'username': AsyncMock(value='invaliduser'),
        'password': AsyncMock(value='short')
    }
    mock_form_service.create_form.return_value = mock_form
    mock_form_service.validate_form.return_value = (False, {'password': ['Password too short']})  # Form is invalid

    # Mock template rendering to simulate rendering an HTML response with errors
    mock_template_service.render_template.return_value = "<html>Form with errors</html>"

    # Mock the response to return a Response object when send_response is called
    mock_response = Response(content="<html>Form with errors</html>", status_code=400, content_type='text/html')
    mock_send_response.return_value = mock_response

    # Monkeypatch the DI container to return the mocked services
    async def mock_get(service_name):
        services = {
            'TemplateService': mock_template_service,
            'FormService': mock_form_service,
            'AuthenticationService': mock_authentication_service,
            'SessionService': mock_session_service,
            'EventBus': mock_event_bus,
        }
        return services[service_name]

    monkeypatch.setattr(container, 'get', mock_get)

    # Monkeypatch HTTPController's send_response to track the response flow
    monkeypatch.setattr(HTTPController, 'send_response', mock_send_response)

    # Mock request with POST method and form data
    mock_request = AsyncMock()
    mock_request.method = "POST"
    mock_request.form.return_value = {
        'username': 'invaliduser',
        'password': 'short'  # Simulate invalid data
    }
    mock_send = AsyncMock()

    # Create the event object and include the 'send' key
    event = Event(name='http.request.received', data={
        'request': mock_request,
        'send': mock_send,  # Mocked send function for HTTPController
    })

    # Call the login_controller
    await login_controller(event, form_service=mock_form_service, template_service=mock_template_service,
                           auth_service=mock_authentication_service, session_service=mock_session_service,
                           event_bus=mock_event_bus)

    # Check that the form service was used to create and validate the form
    mock_form_service.create_form.assert_called_once_with(ANY, data={'username': 'invaliduser', 'password': 'short'})
    mock_form_service.validate_form.assert_called_once_with(mock_form)

    # Ensure the response was sent
    mock_send_response.assert_called_once()

    # Extract the response object from the call args
    response = mock_send_response.call_args[0][0]  # First positional arg is the response object

    # Since template rendering is synchronous, no need to await
    content = response.content

    # Check response content and status
    assert response.content_type == 'text/html'
    assert content == "<html>Form with errors</html>"  # Check the mocked content
    assert response.status_code == 400  # Should return a 400 status for invalid form

    # Check that the correct template was rendered with errors
    mock_template_service.render_template.assert_called_once_with('login.html', {
        'form': mock_form,
        'errors': {'password': ['Password too short']}
    })
