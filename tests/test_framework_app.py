import pytest
import traceback
from unittest.mock import AsyncMock, Mock

from src.core.framework_app import FrameworkApp
from src.dicontainer import di_container


@pytest.mark.asyncio
async def test_framework_app_lifespan(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()

    # Mock the handle_lifespan_events function
    mock_handle_lifespan_events = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.handle_lifespan_events', mock_handle_lifespan_events)

    scope = {'type': 'lifespan'}
    app = FrameworkApp()

    # Call the app with a lifespan event
    await app(scope, receive, send)

    # Ensure the lifespan handler was called
    mock_handle_lifespan_events.assert_awaited_once_with(scope, receive, send)


@pytest.mark.asyncio
async def test_framework_app_http(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()

    # Mock Request class and handle_http_requests function
    mock_request = Mock()  # Use Mock for Request
    monkeypatch.setattr('src.core.framework_app.Request', mock_request)

    mock_handle_http_requests = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.handle_http_requests', mock_handle_http_requests)

    scope = {'type': 'http'}
    app = FrameworkApp()

    # Call the app with an HTTP event
    await app(scope, receive, send)

    # Ensure the http request handler was called with the correct arguments
    mock_handle_http_requests.assert_awaited_once_with(scope, receive, send, mock_request.return_value, di_container)


@pytest.mark.asyncio
async def test_framework_app_websocket(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()

    # Mock Request class and handle_websocket_connections function
    mock_request = Mock()
    monkeypatch.setattr('src.core.framework_app.Request', mock_request)

    mock_handle_websocket_connections = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.handle_websocket_connections', mock_handle_websocket_connections)

    scope = {'type': 'websocket'}
    app = FrameworkApp()

    # Call the app with a WebSocket event
    await app(scope, receive, send)

    # Ensure the websocket handler was called with the correct arguments
    mock_handle_websocket_connections.assert_awaited_once_with(scope, receive, send, mock_request.return_value, di_container)


@pytest.mark.asyncio
async def test_framework_app_exception_handling(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()

    # Mock EventBus and Event
    mock_event = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.Event', mock_event)

    # Ensure event_bus.publish is an AsyncMock
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()  # Explicitly set publish as an AsyncMock
    mock_get = AsyncMock(return_value=event_bus)
    monkeypatch.setattr('src.core.framework_app.di_container.get', mock_get)

    # Force handle_http_requests to raise an exception
    mock_handle_http_requests = AsyncMock(side_effect=Exception("Test exception"))
    monkeypatch.setattr('src.core.framework_app.handle_http_requests', mock_handle_http_requests)

    scope = {'type': 'http'}
    app = FrameworkApp()

    # Call the app with an HTTP event that raises an exception
    await app(scope, receive, send)

    # Debugging: Check if event_bus.publish is an AsyncMock
    print(f"event_bus.publish: {event_bus.publish}")

    # Ensure the publish method was awaited once
    event_bus.publish.assert_awaited_once()

    # Capture the actual traceback that would be generated
    captured_traceback = traceback.format_exc()

    # Check that the error event was published with the correct partial traceback
    mock_event.assert_called_once()

    # Extract the actual arguments passed to the mock event
    args, kwargs = mock_event.call_args

    # Verify the name of the event
    assert kwargs['name'] == "http.error.500"

    # Check that the exception is correctly passed
    assert kwargs['data']['exception'] == mock_handle_http_requests.side_effect

    # Ensure the traceback contains the exception message (partial match)
    assert "Test exception" in kwargs['data']['traceback']
    assert "raise effect" in kwargs['data']['traceback']

    # Ensure that send was passed correctly
    assert kwargs['data']['send'] == send
