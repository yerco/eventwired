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
async def test_login_controller_post_success_full():
    # Step 1: Initialize the DI container and ORMService
    orm_service = await di_container.get('ORMService')
    await orm_service.init()  # Ensure ORM is initialized and connected to the database

    # Optionally, make sure tables are created (if necessary for the test)
    await orm_service.create_tables()

    # Step 2: Hash the password before storing it
    password_service = await di_container.get('PasswordService')
    hashed_password = password_service.hash_password('validpassword')

    # Ensure the user exists in the database with a hashed password
    await orm_service.create(User, username='validuser', password=hashed_password)

    # Step 3: Create a mock form data representing the body of a POST request
    async def mock_receive():
        return {
            'body': b'username=validuser&password=validpassword',
            'more_body': False
        }

    # Step 4: Create a Request object simulating a real POST request
    request = Request(scope={'method': 'POST'}, receive=mock_receive)

    # Step 5: Prepare the event with real DI container and other dependencies
    event = Event(name='http.request.received', data={
        'request': request,
        'send': AsyncMock(),  # Mock the send function for the ASGI response
        'session': None
    })

    # Step 6: Call the login_controller with the real container
    await login_controller(event)

    # Step 7: Extract and assert the response from the event
    response = event.data.get('response')

    # Ensure the response is successful
    assert response is not None
    assert response.status_code == 200
    assert "Login successful" in response.content
    assert response.content_type == 'text/plain'

    os.remove('default.db')


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
