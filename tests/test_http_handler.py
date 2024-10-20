import pytest
from unittest.mock import AsyncMock
from src.core.event_bus import Event
from src.core.http_handler import handle_http_requests
from src.services.middleware_service import MiddlewareService


@pytest.mark.asyncio
async def test_handle_http_requests_success():
    # Step 1: Mock dependencies
    mock_event_bus = AsyncMock()
    mock_middleware_service = AsyncMock(MiddlewareService)
    mock_send = AsyncMock()
    mock_receive = AsyncMock()
    mock_request = AsyncMock()

    # Step 2: Mock the DI container to return the EventBus and MiddlewareService
    mock_di_container = AsyncMock()
    mock_di_container.get.side_effect = lambda service_name: {
        'EventBus': mock_event_bus,
        'MiddlewareService': mock_middleware_service
    }[service_name]

    # Step 3: Mock the scope (path, method, etc.)
    scope = {'path': '/test', 'method': 'GET'}

    # Ensure the middleware doesn't block the final handler by simulating successful execution
    async def mock_middleware_execute(event: Event, handler):
        await handler(event)  # Simulate calling the final handler

    # Step 4: Set the middleware to call the handler after execution
    mock_middleware_service.execute.side_effect = mock_middleware_execute

    # Step 5: Call the handle_http_requests function
    await handle_http_requests(scope, mock_receive, mock_send, mock_request, mock_di_container)

    # Step 6: Assert that middleware_service.execute was called
    mock_middleware_service.execute.assert_called_once()

    # Step 7: Assert that event_bus.publish was called twice
    assert mock_event_bus.publish.call_count == 2

    # Step 8: Check the first event (http.request.received)
    event_received = mock_event_bus.publish.call_args_list[0][0][0]  # Get the first event argument
    assert isinstance(event_received, Event)
    assert event_received.name == 'http.request.received'
    assert event_received.data['scope'] == scope
    assert event_received.data['receive'] == mock_receive
    assert event_received.data['send'] == mock_send
    assert event_received.data['request'] == mock_request

    # Step 9: Check the second event (http.request.completed)
    event_completed = mock_event_bus.publish.call_args_list[1][0][0]  # Get the second event argument
    assert isinstance(event_completed, Event)
    assert event_completed.name == 'http.request.completed'
    assert event_completed.data['scope'] == scope
    assert event_completed.data['receive'] == mock_receive
    assert event_completed.data['send'] == mock_send
    assert event_completed.data['request'] == mock_request


@pytest.mark.asyncio
async def test_handle_http_requests_middleware_failure():
    mock_event_bus = AsyncMock()
    mock_middleware_service = AsyncMock(MiddlewareService)
    mock_send = AsyncMock()  # Ensure this is AsyncMock
    mock_receive = AsyncMock()
    mock_request = AsyncMock()

    mock_middleware_service.execute.side_effect = Exception("Middleware Failure")

    mock_di_container = AsyncMock()
    mock_di_container.get.side_effect = lambda service_name: {
        'EventBus': mock_event_bus,
        'MiddlewareService': mock_middleware_service
    }[service_name]

    scope = {'path': '/test', 'method': 'GET'}

    await handle_http_requests(scope, mock_receive, mock_send, mock_request, mock_di_container)

    # Assert that the 500 error event was published with the expected data
    assert mock_event_bus.publish.called, "The event bus did not publish any events."
    actual_event = mock_event_bus.publish.call_args[0][0]
    assert actual_event.name == 'http.error.500'
    assert 'exception' in actual_event.data
    assert 'traceback' in actual_event.data
    assert actual_event.data['exception'].args[0] == "Middleware Failure"
