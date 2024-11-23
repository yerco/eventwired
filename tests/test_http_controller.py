import pytest
from unittest.mock import AsyncMock

from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController
from src.core.response import Response
from src.services.middleware_service import MiddlewareService


@pytest.mark.asyncio
async def test_send_response_with_middleware(monkeypatch):
    # Step 1: Mock the send function
    mock_send = AsyncMock()
    mock_event_bus = AsyncMock()

    # Step 2: Create an event with the mock send function in the data
    event = Event(name='test_event', data={'send': mock_send})

    # Step 3: Initialize the BaseController with the event
    controller = HTTPController(event)

    # Step 4: Create a Response object
    response = Response(content="Test Response", status_code=200, content_type="text/plain")

    # Step 5: Monkeypatch the response's send method to track calls
    mock_response_send = AsyncMock()
    monkeypatch.setattr(response, 'send', mock_response_send)

    # Step 6: Call send_response with the Response object
    await controller.send_response(response)

    # Step 7: Ensure the response was stored in the event data
    assert event.data['response'] == response

    # Step 8: Simulate middleware service to execute and handle the response sending
    middleware_service = MiddlewareService(event_bus=mock_event_bus)

    # Call the middleware execute function to simulate full flow, and pass a simple handler
    async def mock_handler(ev):
        pass

    await middleware_service.execute(event, mock_handler)

    # Step 9: Ensure the response's send method was called with the mock send function
    mock_response_send.assert_called_once_with(mock_send)


@pytest.mark.asyncio
async def test_send_response_with_mocked_middleware(monkeypatch):
    # Step 1: Mock the send function
    mock_send = AsyncMock()

    # Step 2: Create an event with the mock send function in the data
    event = Event(name='test_event', data={'send': mock_send})

    # Step 3: Initialize the BaseController with the event
    controller = HTTPController(event)

    # Step 4: Create a Response object
    response = Response(content="Test Response", status_code=200, content_type="text/plain")

    # Step 5: Monkeypatch the response's send method to track calls
    mock_response_send = AsyncMock()
    monkeypatch.setattr(response, 'send', mock_response_send)

    # Step 6: Define a mock handler function to represent controller logic
    async def mock_handler(ev: Event):
        # Simulate controller logic that sets the response in the event
        await controller.send_response(response)

    # Step 7: Mock the MiddlewareService execution flow
    mock_middleware_service = AsyncMock()

    # Simulate middleware execution, which would call the response send
    async def mock_middleware_execute(event, handler):
        await handler(event)  # Simulate the controller logic
        # Simulate the middleware after_request phase calling response.send()
        response = event.data['response']
        await response.send(mock_send)

    mock_middleware_service.execute.side_effect = mock_middleware_execute

    # Step 8: Execute the mocked middleware
    await mock_middleware_service.execute(event, mock_handler)

    # Step 9: Ensure the response was stored in the event data
    assert event.data['response'] == response

    # Step 10: Ensure the response's send method was called with the mock send function
    mock_response_send.assert_called_once_with(mock_send)


@pytest.mark.asyncio
async def test_send_text():
    mock_send = AsyncMock()
    event = Event(name='test_event', data={'send': mock_send})
    controller = HTTPController(event)

    await controller.send_text("Hello, World!")

    # Ensure response is in event data
    response = event.data['response']
    assert response.content == "Hello, World!"
    assert response.status_code == 200
    assert response.content_type == 'text/plain'

    # Check that the response has been correctly created
    assert isinstance(response, Response)


@pytest.mark.asyncio
async def test_send_html():
    mock_send = AsyncMock()
    event = Event(name='test_event', data={'send': mock_send})
    controller = HTTPController(event)

    await controller.send_html("<h1>Hello</h1>")

    # Ensure response is in event data
    response = event.data['response']
    assert response.content == "<h1>Hello</h1>"
    assert response.status_code == 200
    assert response.content_type == 'text/html'

    # Check that the response has been correctly created
    assert isinstance(response, Response)


@pytest.mark.asyncio
async def test_send_json():
    mock_send = AsyncMock()
    event = Event(name='test_event', data={'send': mock_send})
    controller = HTTPController(event)

    await controller.send_json({"key": "value"})

    # Ensure response is in event data
    response = event.data['response']
    assert response.content == {"key": "value"}
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    # Check that the response has been correctly created
    assert isinstance(response, Response)


@pytest.mark.asyncio
async def test_send_error():
    mock_send = AsyncMock()
    event = Event(name='test_event', data={'send': mock_send})
    controller = HTTPController(event)

    await controller.send_error(404, "Not Found")

    # Ensure response is in event data
    response = event.data['response']
    assert response.content == "Not Found"
    assert response.status_code == 404
    assert response.content_type == 'text/plain'

    # Check that the response has been correctly created
    assert isinstance(response, Response)
