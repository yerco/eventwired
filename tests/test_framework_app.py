import pytest
from unittest.mock import AsyncMock, Mock

from src.core.framework_app import FrameworkApp


@pytest.mark.asyncio
async def test_framework_app_lifespan(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()
    container = AsyncMock()

    # Mock the handle_lifespan_events function
    mock_handle_lifespan_events = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.handle_lifespan_events', mock_handle_lifespan_events)

    scope = {'type': 'lifespan'}
    app = FrameworkApp(container=container, register_routes=AsyncMock(), user_setup=AsyncMock())

    # Call the app with a lifespan event
    await app(scope, receive, send)

    # Ensure the lifespan handler was called
    mock_handle_lifespan_events.assert_awaited_once_with(scope, receive, send)


@pytest.mark.asyncio
async def test_framework_app_http(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()
    container = AsyncMock()

    # Mock Request class and handle_http_requests function
    mock_request = Mock()  # Use Mock for Request
    monkeypatch.setattr('src.core.framework_app.Request', mock_request)

    mock_handle_http_requests = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.handle_http_requests', mock_handle_http_requests)

    scope = {'type': 'http'}
    app = FrameworkApp(container=container, register_routes=AsyncMock(), user_setup=AsyncMock())

    # Call the app with an HTTP event
    await app(scope, receive, send)

    # Ensure the http request handler was called with the correct arguments
    mock_handle_http_requests.assert_awaited_once_with(scope, receive, send, mock_request.return_value, container)


@pytest.mark.asyncio
async def test_framework_app_websocket(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()
    container = AsyncMock()

    # Mock Request class and handle_websocket_connections function
    mock_request = Mock()
    monkeypatch.setattr('src.core.framework_app.Request', mock_request)

    mock_handle_websocket_connections = AsyncMock()
    monkeypatch.setattr('src.core.framework_app.handle_websocket_connections', mock_handle_websocket_connections)

    scope = {'type': 'websocket'}
    app = FrameworkApp(container=container, register_routes=AsyncMock(), user_setup=AsyncMock())

    # Call the app with a WebSocket event
    await app(scope, receive, send)

    # Ensure the websocket handler was called with the correct arguments
    mock_handle_websocket_connections.assert_awaited_once_with(scope, receive, send, mock_request.return_value, container)


@pytest.mark.asyncio
async def test_framework_app_exception_handling(monkeypatch):
    receive = AsyncMock()
    send = AsyncMock()
    container = AsyncMock()

    mock_event_bus = AsyncMock()
    async def mock_get(service_name):
        if service_name == "EventBus":
            return mock_event_bus
        raise Exception(f"Service {service_name} not found")
    container.get = AsyncMock(side_effect=mock_get)

    # Mock Event class to return a proper instance
    class MockEvent:
        def __init__(self, name, data):
            self.name = name
            self.data = data

    mock_event_cls = Mock(side_effect=MockEvent)  # Wrap MockEvent with Mock

    monkeypatch.setattr('src.core.framework_app.Event', mock_event_cls)

    mock_event_bus.publish = AsyncMock()

    # Force handle_http_requests to raise an exception
    mock_handle_http_requests = AsyncMock(side_effect=Exception("Test exception"))
    monkeypatch.setattr('src.core.framework_app.handle_http_requests', mock_handle_http_requests)

    scope = {'type': 'http'}
    app = FrameworkApp(container=container, register_routes=AsyncMock(), user_setup=AsyncMock())

    # Call the app with an HTTP event that raises an exception
    await app(scope, receive, send)

    # Ensure the error event was published# Fetch the actual call arguments to MockEvent
    actual_args, actual_kwargs = mock_event_cls.call_args
    # Assert the arguments explicitly
    assert actual_kwargs['name'] == "http.error.500"  # Event name
    assert type(actual_kwargs['data']['exception']) is Exception  # Event data
    assert "Traceback" in actual_kwargs['data']['traceback']  # Traceback exists
    assert actual_kwargs['data']['send'] == send  # Correct send function


    # Ensure the publish method was awaited once
    mock_event_bus.publish.assert_awaited_once()
