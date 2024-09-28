import pytest

from unittest.mock import AsyncMock, call, Mock
from demo_app.controllers.chat_room_controller import chat_room_controller
from src.controllers.base_controller import BaseController
from src.event_bus import Event
from src.services.websocket_service import WebSocketService


@pytest.mark.asyncio
async def test_chat_room_controller_initialization(monkeypatch):
    # Test if controller is correctly initialized and set in WebSocketService
    websocket_service = WebSocketService()
    websocket_service.clients = []

    mock_send = AsyncMock()
    event = Event(name="test_event", data={'send': mock_send, 'receive': AsyncMock()})

    # Use monkeypatch to mock the DI container
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Call the chat_room_controller with the event
    await chat_room_controller(event)

    # Assert that the controller is added to the clients list
    assert len(websocket_service.clients) == 1, "Controller was not added to clients list"
    assert isinstance(websocket_service.clients[0], BaseController), "The client added is not of correct type"


@pytest.mark.asyncio
async def test_chat_room_controller_connection(monkeypatch):
    # Test if the connection is established correctly by checking if the client accepts the websocket
    websocket_service = WebSocketService()
    websocket_service.clients = []

    mock_send = AsyncMock()
    mock_receive = AsyncMock()
    event = Event(name="test_event", data={'send': mock_send, 'receive': mock_receive})

    # Use the real BaseController
    controller = BaseController(event)
    websocket_service.set_controller(controller)

    # Use monkeypatch to mock the DI container and inject the websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Call the chat_room_controller
    await websocket_service.start(controller)

    assert controller.connection_accepted is True, "The WebSocket connection was not established correctly."


@pytest.mark.asyncio
async def test_chat_room_controller_broadcast_success(monkeypatch):
    # Test the behavior when listening for messages and ensure proper processing/broadcasting
    websocket_service = WebSocketService()
    websocket_service.clients = []

    # Set up the event with mocked `send` and `receive`
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Mocking `receive` to simulate a user message
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello World!'},
        {'type': 'websocket.disconnect'}
    ]
    event = Event(name="test_event", data={'send': mock_send, 'receive': mock_receive})

    # Use the real BaseController
    controller = BaseController(event)
    websocket_service.set_controller(controller)

    # Use monkeypatch to mock the DI container and inject the websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Mock the broadcast_message method to track if it's being called
    mock_broadcast_message = AsyncMock()
    monkeypatch.setattr(websocket_service, 'broadcast_message', mock_broadcast_message)

    # Start the WebSocket connection (calls `accept_websocket`)
    await websocket_service.start(controller)
    assert controller.connection_accepted is True, "The WebSocket connection was not established correctly."

    async def on_message(message):
        # Filter out WebSocket connect/disconnect events from broadcasting
        if message not in {"websocket.connect", "websocket.disconnect"}:
            # Process and respond to the message
            broadcast_message = f"{message}"
            await websocket_service.broadcast_message(broadcast_message)

    # _listen call as listen is just a wrapping loop around _listen
    await websocket_service._listen(controller, on_message)

    assert mock_broadcast_message.call_count == 1, "broadcast_message was not called as expected"


@pytest.mark.asyncio
async def test_chat_room_controller_send_websocket_message_success(monkeypatch):
    # Test the behavior when listening for messages and ensure proper processing/broadcasting
    websocket_service = WebSocketService()
    websocket_service.clients = []

    # Set up the event with mocked `send` and `receive`
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Mocking `receive` to simulate a user message
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello World!'},
        {'type': 'websocket.disconnect'}
    ]
    event = Event(name="test_event", data={'send': mock_send, 'receive': mock_receive})

    # Use the real BaseController
    controller = BaseController(event)
    websocket_service.set_controller(controller)

    # Use monkeypatch to mock the DI container and inject the websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Mock the broadcast_message method to track if it's being called
    mock_send_websocket_message = AsyncMock()
    monkeypatch.setattr(controller, 'send_websocket_message', mock_send_websocket_message)

    # Start the WebSocket connection (calls `accept_websocket`)
    await websocket_service.start(controller)
    assert controller.connection_accepted is True, "The WebSocket connection was not established correctly."

    async def on_message(message):
        # Filter out WebSocket connect/disconnect events from broadcasting
        if message not in {"websocket.connect", "websocket.disconnect"}:
            # Process and respond to the message
            broadcast_message = f"User: {message}"
            await websocket_service.broadcast_message(broadcast_message)

    # _listen call as listen is just a wrapping loop around _listen
    await websocket_service._listen(controller, on_message)

    assert mock_send_websocket_message.call_count == 1, "send_websocket_message was not called as expected"

    # Assert that the message sent matches what we expect
    mock_send_websocket_message.assert_called_once_with("User: Hello World!")


@pytest.mark.asyncio
async def test_chat_room_controller_send_message_success(monkeypatch):
    # Test the behavior when listening for messages and ensure proper processing/broadcasting
    websocket_service = WebSocketService()
    websocket_service.clients = []

    # Set up the event with mocked `send` and `receive`
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Mocking `receive` to simulate a user message
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello World!'},
        {'type': 'websocket.disconnect'}
    ]
    event = Event(name="test_event", data={'send': mock_send, 'receive': mock_receive})

    # Use the real BaseController
    controller = BaseController(event)
    websocket_service.set_controller(controller)

    # Use monkeypatch to mock the DI container and inject the websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Start the WebSocket connection (calls `accept_websocket`)
    await websocket_service.start(controller)
    assert controller.connection_accepted is True, "The WebSocket connection was not established correctly."

    async def on_message(message):
        # Filter out WebSocket connect/disconnect events from broadcasting
        if message not in {"websocket.connect", "websocket.disconnect"}:
            # Process and respond to the message
            broadcast_message = f"User: {message}"
            await websocket_service.broadcast_message(broadcast_message)

    # _listen call as listen is just a wrapping loop around _listen
    await websocket_service._listen(controller, on_message)

    print(f"mock_send.call_args_list: {mock_send.call_args_list}")
    # Assert that the message sent matches what we expect
    mock_send.assert_any_call({
        'type': 'websocket.send',
        'text': 'User: Hello World!'
    })


@pytest.mark.asyncio
async def test_chat_room_controller_stop_invoked(monkeypatch):
    # Test the behavior when listening for messages and ensure proper processing/broadcasting
    websocket_service = WebSocketService()
    websocket_service.clients = []

    # Set up the event with mocked `send` and `receive`
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Mocking `receive` to simulate a user message
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello World!'},
        {'type': 'websocket.disconnect'}
    ]
    event = Event(name="test_event", data={'send': mock_send, 'receive': mock_receive})

    # Use the real BaseController
    controller = BaseController(event)
    websocket_service.set_controller(controller)

    # Use monkeypatch to mock the DI container and inject the websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))

    # Start the WebSocket connection (calls `accept_websocket`)
    await websocket_service.start(controller)
    assert controller.connection_accepted is True, "The WebSocket connection was not established correctly."

    async def on_message(message):
        # Filter out WebSocket connect/disconnect events from broadcasting
        if message not in {"websocket.connect", "websocket.disconnect"}:
            # Process and respond to the message
            broadcast_message = f"User: {message}"
            await websocket_service.broadcast_message(broadcast_message)

    # _listen call as listen is just a wrapping loop around _listen
    await websocket_service.listen(controller, on_message)

    # Assert that the WebSocket was properly closed after the disconnect message
    mock_send.assert_any_call({
        'type': 'websocket.close',
        'code': 1000  # Normal closure
    })

    # Additionally, ensure that the stop method sets `connection_accepted` to False
    assert controller.connection_accepted is False, "The WebSocket connection was not properly closed."


# @pytest.mark.asyncio
# async def test_chat_room_controller_broadcast_to_multiple_clients(monkeypatch):
#     # Create a WebSocketService instance
#     websocket_service = WebSocketService()
#     websocket_service.clients = []
#
#     # Mock send and receive for two clients
#     mock_send_1 = AsyncMock()
#     mock_receive_1 = AsyncMock()
#     mock_send_2 = AsyncMock()
#     mock_receive_2 = AsyncMock()
#
#     # Mocking `receive` to simulate user messages
#     mock_receive_1.side_effect = [
#         {'type': 'websocket.receive', 'text': 'Hello from client 1'},
#         {'type': 'websocket.disconnect'}
#     ]
#     mock_receive_2.side_effect = [
#         {'type': 'websocket.receive', 'text': 'Hello from client 2'},
#         {'type': 'websocket.disconnect'}
#     ]
#
#     # Set up the events for two clients
#     event_1 = Event(name="test_event_1", data={'send': mock_send_1, 'receive': mock_receive_1})
#     event_2 = Event(name="test_event_2", data={'send': mock_send_2, 'receive': mock_receive_2})
#
#     # Create controllers for both clients and add them to WebSocketService
#     controller_1 = BaseController(event_1)
#     controller_2 = BaseController(event_2)
#     websocket_service.set_controller(controller_1)
#     websocket_service.set_controller(controller_2)
#
#     # Use monkeypatch to mock the DI container and inject the websocket_service
#     monkeypatch.setattr('demo_app.di_setup.di_container.get', AsyncMock(return_value=websocket_service))
#
#     # Start WebSocket connections for both clients
#     await websocket_service.start(controller_1)
#     await websocket_service.start(controller_2)
#     assert controller_1.connection_accepted is True, "The WebSocket connection was not established correctly for client 1."
#     assert controller_2.connection_accepted is True, "The WebSocket connection was not established correctly for client 2."
#
#     async def on_message(message):
#         # Filter out WebSocket connect/disconnect events from broadcasting
#         if message not in {"websocket.connect", "websocket.disconnect"}:
#             # Process and respond to the message
#             broadcast_message = f"User: {message}"
#             await websocket_service.broadcast_message(broadcast_message)
#
#     # Simulate listening for messages
#     await websocket_service._listen(controller_1, on_message)
#     await websocket_service._listen(controller_2, on_message)
#
#     # Assert that client 2 received the message from client 1
#     mock_send_2.assert_any_call({
#         'type': 'websocket.send',
#         'text': 'User: Hello from client 1'
#     })
#
#     # Assert that client 1 received the message from client 2
#     mock_send_1.assert_any_call({
#         'type': 'websocket.send',
#         'text': 'User: Hello from client 2'
#     })
#
#     await websocket_service.broadcast_shutdown()
#     # Assert that the WebSockets were properly closed
#     #mock_send_1.assert_any_call({'type': 'websocket.close', 'code': 1000})
#     #mock_send_2.assert_any_call({'type': 'websocket.close', 'code': 1000})
#
#     # Ensure that both controllers are correctly closed
#     assert controller_1.connection_accepted is False, "The WebSocket connection was not properly closed for client 1."
#     assert controller_2.connection_accepted is False, "The WebSocket connection was not properly closed for client 2."
