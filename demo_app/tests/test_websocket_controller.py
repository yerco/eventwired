import pytest
from unittest.mock import AsyncMock, patch, Mock

from src.event_bus import Event
from src.controllers.base_controller import BaseController

from demo_app.controllers.websocket_controller import websocket_controller
from src.services.websocket_service import WebSocketService


@pytest.mark.asyncio
@patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock)
async def test_websocket_lifecycle(mock_get):
    # Create mock objects for WebSocketService
    mock_websocket_service = AsyncMock()
    mock_websocket_service.set_controller = Mock()

    # Mock the DI container to return the mocked WebSocketService
    mock_get.return_value = mock_websocket_service

    # Simulate an event for the controller, including 'send' and 'receive' in event.data
    event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Assert the WebSocketService methods were called
    assert isinstance(mock_websocket_service.set_controller.call_args[0][0], BaseController)
    mock_websocket_service.start.assert_called_once()
    mock_websocket_service.listen.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_message_handling(monkeypatch):
    # Mock objects for WebSocketService and controller
    mock_websocket_service = AsyncMock()
    mock_send = AsyncMock()

    # Simulate an event with 'send' and 'receive' in event.data
    event = Event(name="test_event", data={'send': mock_send, 'receive': AsyncMock()})

    mock_websocket_service.set_controller = Mock()
    # Use monkeypatch to mock the DI container
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=mock_websocket_service))

    # Mock the WebSocketService listen method
    async def mock_listen(on_message):
        # Call the on_message function as if a message was received
        await on_message("test_message")

    mock_websocket_service.listen.side_effect = mock_listen

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Ensure that 'send' (event.data['send']) was called with the processed message
    mock_send.assert_called_once_with({
        'type': 'websocket.send',
        'text': 'Processed: test_message'
    })


@pytest.mark.asyncio
@patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock)
async def test_websocket_service_resolution_error(mock_get):
    # Simulate DI container failing to resolve WebSocketService
    mock_get.side_effect = Exception("Service not found")

    # Simulate an event
    event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Call the websocket_controller and ensure it handles the error
    with pytest.raises(Exception) as exc_info:
        await websocket_controller(event)

    assert str(exc_info.value) == "Service not found"


@pytest.mark.asyncio
async def test_websocket_graceful_shutdown(monkeypatch):
    # Create a real WebSocketService instance
    websocket_service = WebSocketService()
    websocket_service.controller = AsyncMock()

    # Mock the on_message handler
    on_message = AsyncMock()

    # Mock the _listen method to simulate breaking the loop or an exception
    async def mock_listen(on_message):
        raise Exception("Simulated exception during listen")

    monkeypatch.setattr(websocket_service, "_listen", mock_listen)

    # Mock the stop method to track its call
    mock_stop = AsyncMock()
    monkeypatch.setattr(websocket_service, "stop", mock_stop)

    # Call the listen method and expect an exception
    try:
        await websocket_service.listen(on_message)
    except Exception as e:
        assert str(e) == "Simulated exception during listen"

    # Ensure stop is called in the finally block
    mock_stop.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_controller_calls_start(monkeypatch):
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate a basic WebSocket message and disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Mock the WebSocketService
    mock_websocket_service = AsyncMock()
    mock_websocket_service.set_controller = Mock()

    # Use monkeypatch to mock the DI container get method
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=mock_websocket_service))

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Verify that start() was called once
    mock_websocket_service.start.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_controller_calls_set_controller_and_accept_websocket(monkeypatch):
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate a basic WebSocket message and disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Import WebSocketService
    from src.services.websocket_service import WebSocketService

    # Create an instance of WebSocketService
    websocket_service = WebSocketService()

    # Mock BaseController's accept_websocket method
    mock_accept_websocket = AsyncMock(return_value=None)  # Ensure return_value is set

    # Create a mock controller (BaseController)
    mock_controller = Mock(spec=BaseController)

    # Set the mock method explicitly
    mock_controller.accept_websocket = mock_accept_websocket

    # Use monkeypatch to mock the DI container get method
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Explicitly set the mock controller in WebSocketService before calling start()
    websocket_service.set_controller(mock_controller)

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Verify that the controller was set in the WebSocketService
    assert websocket_service.controller is not None, "Controller was not set in WebSocketService"
    assert isinstance(websocket_service.controller, BaseController), "Controller is not an instance of BaseController"

    # Ensure the method was awaited
    await mock_controller.accept_websocket()

    # Verify that accept_websocket was called on the mock controller
    mock_controller.accept_websocket.assert_awaited_once()

    mock_controller.accept_websocket.assert_awaited()



@pytest.mark.asyncio
async def test_websocket_controller_message_processing(monkeypatch):
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate receiving a message and a disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello WebSocket!'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Import WebSocketService
    from src.services.websocket_service import WebSocketService

    # Create an instance of WebSocketService
    websocket_service = WebSocketService()

    # Mock BaseController's accept_websocket method
    mock_accept_websocket = AsyncMock()

    # Create a mock controller (BaseController)
    mock_controller = Mock(spec=BaseController)

    # Set the mock method explicitly
    mock_controller.accept_websocket = mock_accept_websocket

    # Use monkeypatch to mock the DI container get method
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Explicitly set the mock controller in WebSocketService
    websocket_service.set_controller(mock_controller)

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Verify that the controller was set in the WebSocketService
    assert websocket_service.controller is not None, "Controller was not set in WebSocketService"
    assert isinstance(websocket_service.controller, BaseController), "Controller is not an instance of BaseController"

    # Ensure the method was awaited
    await mock_controller.accept_websocket()

    # Verify that accept_websocket was called on the mock controller
    mock_controller.accept_websocket.assert_awaited_once()

    # Verify that the message was processed and sent back
    mock_send.assert_any_call({
        'type': 'websocket.send',
        'text': 'Processed: Hello WebSocket!'
    })

    # Verify that the WebSocket was closed after disconnect
    mock_send.assert_any_call({
        'type': 'websocket.close',
        'code': 1000
    })


@pytest.mark.asyncio
async def test_websocket_controller_ping_pong(monkeypatch):
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate receiving a ping message and a disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'ping'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Import WebSocketService
    from src.services.websocket_service import WebSocketService

    # Create an instance of WebSocketService
    websocket_service = WebSocketService()

    # Mock BaseController's accept_websocket method
    mock_accept_websocket = AsyncMock()

    # Create a mock controller (BaseController)
    mock_controller = Mock(spec=BaseController)

    # Set the mock method explicitly
    mock_controller.accept_websocket = mock_accept_websocket

    # Use monkeypatch to mock the DI container get method
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Explicitly set the mock controller in WebSocketService
    websocket_service.set_controller(mock_controller)

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Verify that the controller was set in the WebSocketService
    assert websocket_service.controller is not None, "Controller was not set in WebSocketService"
    assert isinstance(websocket_service.controller, BaseController), "Controller is not an instance of BaseController"

    # Ensure the method was awaited
    await mock_controller.accept_websocket()

    # Verify that accept_websocket was called on the mock controller
    mock_controller.accept_websocket.assert_awaited_once()

    # Verify that the WebSocket responded with pong when it received ping
    mock_send.assert_any_call({
        'type': 'websocket.send',
        'text': 'pong'
    })

    # Verify that the WebSocket was closed after disconnect
    mock_send.assert_any_call({
        'type': 'websocket.close',
        'code': 1000
    })


@pytest.mark.asyncio
async def test_websocket_controller_disconnect(monkeypatch):
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate receiving a disconnect message
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'disconnect'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Import WebSocketService
    from src.services.websocket_service import WebSocketService

    # Create an instance of WebSocketService
    websocket_service = WebSocketService()

    # Mock BaseController's accept_websocket method
    mock_accept_websocket = AsyncMock()

    # Create a mock controller (BaseController)
    mock_controller = Mock(spec=BaseController)

    # Set the mock method explicitly
    mock_controller.accept_websocket = mock_accept_websocket

    # Use monkeypatch to mock the DI container get method
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Explicitly set the mock controller in WebSocketService
    websocket_service.set_controller(mock_controller)

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Verify that the controller was set in the WebSocketService
    assert websocket_service.controller is not None, "Controller was not set in WebSocketService"
    assert isinstance(websocket_service.controller, BaseController), "Controller is not an instance of BaseController"

    # Ensure the method was awaited
    await mock_controller.accept_websocket()

    # Verify that accept_websocket was called on the mock controller
    mock_controller.accept_websocket.assert_awaited_once()

    # Verify that the WebSocket was closed after receiving "disconnect"
    mock_send.assert_any_call({
        'type': 'websocket.close',
        'code': 1000  # Normal closure
    })


@pytest.mark.asyncio
async def test_websocket_controller_exit_message(monkeypatch):
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate receiving an exit message and a disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'exit'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Import WebSocketService
    from src.services.websocket_service import WebSocketService

    # Create an instance of WebSocketService
    websocket_service = WebSocketService()

    # Mock BaseController's accept_websocket method
    mock_accept_websocket = AsyncMock()

    # Create a mock controller (BaseController)
    mock_controller = Mock(spec=BaseController)

    # Set the mock method explicitly
    mock_controller.accept_websocket = mock_accept_websocket

    # Use monkeypatch to mock the DI container get method
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Explicitly set the mock controller in WebSocketService
    websocket_service.set_controller(mock_controller)

    # Call the websocket_controller with the mock event
    await websocket_controller(event)

    # Verify that the controller was set in the WebSocketService
    assert websocket_service.controller is not None, "Controller was not set in WebSocketService"
    assert isinstance(websocket_service.controller, BaseController), "Controller is not an instance of BaseController"

    # Ensure the method was awaited
    await mock_controller.accept_websocket()

    # Verify that accept_websocket was called on the mock controller
    mock_controller.accept_websocket.assert_awaited_once()

    # Verify that the WebSocket sends a shutdown message after receiving "exit"
    mock_send.assert_any_call({
        'type': 'websocket.send',
        'text': 'Server is shutting down. Please reconnect later.'
    })

    # Verify that the WebSocket was closed after receiving "exit"
    mock_send.assert_any_call({
        'type': 'websocket.close',
        'code': 1000  # Normal closure
    })
