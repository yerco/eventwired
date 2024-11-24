import pytest
from unittest.mock import AsyncMock, Mock

import pytest_asyncio

from src.services.websocket_service import WebSocketService
from src.core.dicontainer import di_container


@pytest_asyncio.fixture
def websocket_service():
    service = WebSocketService()
    return service


@pytest_asyncio.fixture(autouse=True, scope="function")
def reset_websocket_service():
    service = WebSocketService()
    service.reset()
    yield
    service.reset()


@pytest_asyncio.fixture(autouse=True, scope="function")
def reset_di_container_fixture():
    di_container.reset()
    yield
    di_container.reset()


def test_add_and_remove_client(websocket_service):
    # Test adding clients
    websocket_service.add_client("client1")
    assert "client1" in websocket_service.clients

    websocket_service.add_client("client2")
    assert "client2" in websocket_service.clients

    # Test removing clients
    websocket_service.remove_client("client1")
    assert "client1" not in websocket_service.clients


@pytest.mark.asyncio
async def test_start_websocket_service(websocket_service):
    di_container.reset()
    mock_controller = AsyncMock()
    websocket_service.register_client(mock_controller)
    mock_controller.connection_accepted = False

    await websocket_service.accept_client_connection(mock_controller)

    mock_controller.accept_websocket.assert_awaited_once(), "WebSocket connection was not accepted."
    assert mock_controller.connection_accepted is True, "Connection state was not updated correctly."


@pytest.mark.asyncio
async def test_stop_websocket_service(websocket_service):
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    await websocket_service.terminate_client_connection(mock_controller)

    mock_controller.close_websocket.assert_awaited_once(), "WebSocket connection was not properly closed."
    assert mock_controller.connection_accepted is False, "Connection state was not updated correctly."


@pytest.mark.asyncio
async def test_listen_websocket_service(websocket_service, monkeypatch):
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
async def test_underscore_listen_websocket_service(websocket_service, monkeypatch):
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate a message and a disconnect event
    mock_controller.receive_websocket_message.side_effect = [
        "Hello World!",
        "disconnect"
    ]

    mock_on_message = AsyncMock()

    # Call the underscore listen method to control the loop
    await websocket_service._listen(mock_controller, mock_on_message)

    # Check that the message was processed
    mock_on_message.assert_called_once_with("Hello World!")
    # Ensure the stop method was not called in this case
    mock_controller.close_websocket.assert_not_called()
    assert mock_controller.connection_accepted is True, "The connection was closed incorrectly."


@pytest.mark.asyncio
async def test_underscore_listen_websocket_service_ping(websocket_service):
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate a ping message
    mock_controller.receive_websocket_message.side_effect = [
        "ping"
    ]

    mock_on_message = AsyncMock()

    # Call the underscore listen method to control the loop
    await websocket_service._listen(mock_controller, mock_on_message)

    # Ensure the ping message was responded to
    mock_controller.send_websocket_message.assert_awaited_once_with("pong")
    # Ensure the on_message method was not called
    mock_on_message.assert_not_called()


@pytest.mark.asyncio
async def test_underscore_listen_websocket_service_disconnect(websocket_service):
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate a disconnect event
    mock_controller.receive_websocket_message.side_effect = [
        "disconnect"
    ]

    mock_on_message = AsyncMock()

    # Call the underscore listen method to control the loop
    should_break = await websocket_service._listen(mock_controller, mock_on_message)

    # Ensure the loop was broken
    assert should_break is True, "The loop should have been broken after receiving a disconnect message."
    # Ensure the on_message method was not called
    mock_on_message.assert_not_called()


@pytest.mark.asyncio
async def test_underscore_listen_websocket_service_no_message(websocket_service):
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate no message received
    mock_controller.receive_websocket_message.side_effect = [
        None
    ]

    mock_on_message = AsyncMock()

    # Call the underscore listen method to control the loop
    should_break = await websocket_service._listen(mock_controller, mock_on_message)

    # Ensure the loop was broken
    assert should_break is True, "The loop should have been broken after receiving no message."
    # Ensure the on_message method was not called
    mock_on_message.assert_not_called()


@pytest.mark.asyncio
async def test_graceful_shutdown(websocket_service):
    mock_controller = AsyncMock()

    await websocket_service.graceful_shutdown(mock_controller)

    mock_controller.send_websocket_message.assert_awaited_once_with(
        "Server is shutting down. Please reconnect later."
    )
    mock_controller.close_websocket.assert_awaited_once()


@pytest.mark.asyncio
async def test_broadcast_message(websocket_service):
    # Create mock clients to add to WebSocketService
    mock_client_1 = Mock()
    mock_client_1.send_websocket_message = AsyncMock()
    mock_client_1.connection_accepted = True

    mock_client_2 = Mock()
    mock_client_2.send_websocket_message = AsyncMock()
    mock_client_2.connection_accepted = True

    # Manually add the mocked client handlers to the WebSocketService
    websocket_service.clients.append(mock_client_1)
    websocket_service.clients.append(mock_client_2)

    # Broadcast message through client handlers
    await websocket_service.broadcast_message("Test Broadcast")

    # Verify each mock client received the broadcast message
    mock_client_1.send_websocket_message.assert_awaited_once_with("Test Broadcast")
    mock_client_2.send_websocket_message.assert_awaited_once_with("Test Broadcast")


@pytest.mark.asyncio
async def test_broadcast_shutdown(websocket_service):
    # Create mock clients for WebSocketService
    mock_client_1 = Mock()
    mock_client_1.send_websocket_message = AsyncMock()
    mock_client_1.connection_accepted = True  # This client has an open connection

    mock_client_2 = Mock()
    mock_client_2.send_websocket_message = AsyncMock()
    mock_client_2.connection_accepted = True  # This client also has an open connection

    mock_client_3 = Mock()
    mock_client_3.send_websocket_message = AsyncMock()
    mock_client_3.connection_accepted = False  # This client already has a closed connection

    # Manually add the mocked client handlers to the WebSocketService
    websocket_service.clients.extend([mock_client_1, mock_client_2, mock_client_3])

    # Call the broadcast_shutdown method
    await websocket_service.broadcast_shutdown()

    # Verify that the connected clients received the shutdown message
    expected_message = "Server is shutting down. Closing connection."
    mock_client_1.send_websocket_message.assert_awaited_once_with(expected_message)
    mock_client_2.send_websocket_message.assert_awaited_once_with(expected_message)

    # Verify that the client with a closed connection did not receive any message
    mock_client_3.send_websocket_message.assert_not_called()

    # Ensure that the clients list was cleared after the shutdown
    assert len(websocket_service.clients) == 0, "Clients list should be cleared after shutdown."


@pytest.mark.asyncio
async def test_listen_websocket_service_error_handling(websocket_service, monkeypatch):
    mock_controller = AsyncMock()
    mock_controller.connection_accepted = True

    # Simulate an exception during message receiving
    mock_controller.receive_websocket_message.side_effect = RuntimeError("Test RuntimeError")

    # Mock stop to confirm if it's called after the error
    mock_stop = AsyncMock()
    monkeypatch.setattr(websocket_service, "terminate_client_connection", mock_stop)

    # Listen should catch the RuntimeError and call stop
    await websocket_service.listen(mock_controller, AsyncMock())

    # Ensure stop was called
    mock_stop.assert_awaited_once_with(mock_controller)
