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
async def test_broadcast_message():
    websocket_service = WebSocketService()

    # Add mock clients (assuming they are WebSocket connections in real usage)
    websocket_service.add_client("client1")
    websocket_service.add_client("client2")

    # Replace print with a proper mock of send_message
    websocket_service.send_message = AsyncMock()

    # Call broadcast_message
    await websocket_service.broadcast_message("Broadcast Message")

    # Assert send_message is called for each client
    websocket_service.send_message.assert_any_call("client1", "Broadcast Message")
    websocket_service.send_message.assert_any_call("client2", "Broadcast Message")
    assert websocket_service.send_message.call_count == 2


@pytest.mark.asyncio
async def test_start_websocket_service():
    # Create a mock controller
    mock_controller = AsyncMock()
    mock_controller.accept_websocket = AsyncMock()

    # Initialize WebSocketService and set controller
    websocket_service = WebSocketService()
    websocket_service.set_controller(mock_controller)

    # Start WebSocketService and assert that accept_websocket is called
    await websocket_service.start()
    mock_controller.accept_websocket.assert_called_once()


@pytest.mark.asyncio
async def test_stop_websocket_service():
    # Create a mock controller
    mock_controller = AsyncMock()
    mock_controller.close_websocket = AsyncMock()
    mock_controller.send_websocket_message = AsyncMock()

    # Initialize WebSocketService and set controller
    websocket_service = WebSocketService()
    websocket_service.set_controller(mock_controller)

    # Manually set connection_accepted to True
    websocket_service.connection_accepted = True

    # Call stop and assert shutdown
    await websocket_service.stop()
    mock_controller.send_websocket_message.assert_called_once_with("Server is shutting down. Please reconnect later.")
    mock_controller.close_websocket.assert_called_once()


@pytest.mark.asyncio
async def test_listen_websocket_service():
    # Create a mock controller
    mock_controller = AsyncMock()
    mock_controller.receive_websocket_message = AsyncMock(side_effect=["ping", "hello", "exit"])

    # Mock the message handler
    mock_on_message = AsyncMock()

    # Initialize WebSocketService and set controller
    websocket_service = WebSocketService()
    websocket_service.set_controller(mock_controller)

    # Call listen and process the messages
    await websocket_service.listen(mock_on_message)

    # Assert the "ping" message was not passed to the handler
    mock_on_message.assert_called_once_with("hello")  # "ping" should be handled internally, "hello" should be passed
    mock_controller.receive_websocket_message.assert_called()  # Ensure messages were received


@pytest.mark.asyncio
async def test_broadcast_shutdown():
    websocket_service = WebSocketService()

    # Add mock clients (assuming they are WebSocket connections in real usage)
    websocket_service.add_client("client1")
    websocket_service.add_client("client2")

    # Replace print with a proper mock of send_message
    websocket_service.send_message = AsyncMock()

    # Call broadcast_shutdown
    await websocket_service.broadcast_shutdown()

    # Assert send_message is called for each client with shutdown message
    websocket_service.send_message.assert_any_call("client1", "Server is shutting down. Closing connection.")
    websocket_service.send_message.assert_any_call("client2", "Server is shutting down. Closing connection.")
    assert websocket_service.send_message.call_count == 2


@pytest.mark.asyncio
async def test_listen_websocket_service_error_handling():
    # Create a mock controller
    mock_controller = AsyncMock()
    mock_controller.receive_websocket_message = AsyncMock(side_effect=["hello", RuntimeError("Test error"), "exit"])

    # Mock the message handler
    mock_on_message = AsyncMock()

    # Initialize WebSocketService and set controller
    websocket_service = WebSocketService()
    websocket_service.set_controller(mock_controller)

    # Call listen and handle the error
    await websocket_service.listen(mock_on_message)

    # Assert that the first message was processed before the error occurred
    mock_on_message.assert_called_once_with("hello")
    mock_controller.receive_websocket_message.assert_called()  # Ensure messages were received
