import pytest
from unittest.mock import AsyncMock, Mock
from src.services.websocket_service import WebSocketService


def test_add_and_remove_client():
    websocket_service = WebSocketService()

    # Test adding clients
    websocket_service.add_client("client1")
    assert "client1" in websocket_service.clients

    websocket_service.add_client("client2")
    assert "client2" in websocket_service.clients

    # Test removing clients
    websocket_service.remove_client("client1")
    assert "client1" not in websocket_service.clients


@pytest.mark.asyncio
async def test_receive_message():
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello WebSocket!'}
    ]

    websocket_service = WebSocketService()
    message = await websocket_service.receive_message(mock_receive)

    assert message == "Hello WebSocket!"


@pytest.mark.asyncio
async def test_send_message():
    mock_send = AsyncMock()

    websocket_service = WebSocketService()
    await websocket_service.send_message(mock_send, "Test Message")

    mock_send.assert_called_once_with({
        'type': 'websocket.send',
        'text': 'Test Message'
    })


@pytest.mark.asyncio
async def test_start_websocket_service():

    websocket_service = WebSocketService()
    mock_controller = AsyncMock()
    websocket_service.set_controller(mock_controller)
    mock_controller.connection_accepted = False

    await websocket_service.start(mock_controller)

    mock_controller.accept_websocket.assert_awaited_once(), "WebSocket connection was not accepted."
    assert mock_controller.connection_accepted is True, "Connection state was not updated correctly."


@pytest.mark.asyncio
async def test_broadcast_message():
    websocket_service = WebSocketService()

    # Create mock clients
    mock_client_1 = AsyncMock()
    mock_client_2 = AsyncMock()

    # Add clients to WebSocketService
    websocket_service.set_controller(mock_client_1)
    websocket_service.set_controller(mock_client_2)

    # Broadcast a message
    await websocket_service.broadcast_message("Test Broadcast")

    # Ensure each client received the broadcast message
    mock_client_1.send_websocket_message.assert_awaited_once_with("Test Broadcast")
    mock_client_2.send_websocket_message.assert_awaited_once_with("Test Broadcast")


@pytest.mark.asyncio
async def test_stop_websocket_service():
    websocket_service = WebSocketService()
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    await websocket_service.stop(mock_controller)

    mock_controller.close_websocket.assert_awaited_once(), "WebSocket connection was not properly closed."
    assert mock_controller.connection_accepted is False, "Connection state was not updated correctly."


@pytest.mark.asyncio
async def test_listen_websocket_service(monkeypatch):
    websocket_service = WebSocketService()
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate a message and a disconnect event
    mock_controller.receive_websocket_message.side_effect = [
        "Hello World!",
        "disconnect"
    ]

    mock_on_message = AsyncMock()

    # Call listen with a controlled loop (essentially two iterations)
    await websocket_service.listen(mock_controller, mock_on_message)

    # Check that the message was processed
    mock_on_message.assert_called_once_with("Hello World!")
    # Ensure the stop method was called to close the WebSocket
    mock_controller.close_websocket.assert_awaited_once()
    assert mock_controller.connection_accepted is False, "The connection was not properly closed after listening."


@pytest.mark.asyncio
async def test_broadcast_shutdown(monkeypatch):
    websocket_service = WebSocketService()

    # Create mock clients with send_websocket_message and close_websocket methods
    mock_client_1 = AsyncMock()
    mock_client_1.connection_accepted = True
    mock_client_1.send_websocket_message = AsyncMock()
    mock_client_1.close_websocket = AsyncMock()

    mock_client_2 = AsyncMock()
    mock_client_2.connection_accepted = True
    mock_client_2.send_websocket_message = AsyncMock()
    mock_client_2.close_websocket = AsyncMock()

    # Add clients to WebSocketService
    websocket_service.set_controller(mock_client_1)
    websocket_service.set_controller(mock_client_2)

    # Mock the print statements to capture the output for assertions
    mock_print = Mock()
    monkeypatch.setattr("builtins.print", mock_print)

    # Broadcast shutdown message
    await websocket_service.broadcast_shutdown()

    # Ensure shutdown message is sent to both clients
    mock_client_1.send_websocket_message.assert_awaited_once_with("Server is shutting down. Closing connection.")
    mock_client_2.send_websocket_message.assert_awaited_once_with("Server is shutting down. Closing connection.")

    # Ensure both clients were closed SRP problem will refactor
    # mock_client_1.close_websocket.assert_awaited_once()
    # mock_client_2.close_websocket.assert_awaited_once()

    # Ensure the correct messages were printed for each client
    mock_print.assert_any_call(f"Notifying {mock_client_1} about server shutdown.")
    mock_print.assert_any_call(f"Notifying {mock_client_2} about server shutdown.")

    # Ensure clients list is cleared after shutdown
    assert len(websocket_service.clients) == 0, "Clients list was not cleared after shutdown."


@pytest.mark.asyncio
async def test_listen_websocket_service_error_handling(monkeypatch):
    websocket_service = WebSocketService()
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate an exception during message receiving
    mock_controller.receive_websocket_message.side_effect = RuntimeError("Test RuntimeError")

    # Mock stop to confirm if it's called after the error
    mock_stop = AsyncMock()
    monkeypatch.setattr(websocket_service, "stop", mock_stop)

    # Listen should catch the RuntimeError and call stop
    await websocket_service.listen(mock_controller, AsyncMock())

    # Ensure stop was called
    mock_stop.assert_awaited_once_with(mock_controller)
