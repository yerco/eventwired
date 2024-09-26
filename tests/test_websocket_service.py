import pytest
from unittest.mock import AsyncMock, Mock
from src.services.websocket_service import WebSocketService


@pytest.mark.asyncio
async def test_default_message_processing():
    websocket_service = WebSocketService()

    # Test default message processor
    message = "Hello"
    result = await websocket_service.process_message(message)
    assert result == f"Echo: {message}"


@pytest.mark.asyncio
async def test_custom_message_processing():
    # Custom message processor mock
    async def custom_processor(message: str) -> str:
        return f"Custom: {message}"

    websocket_service = WebSocketService(message_processor=custom_processor)

    # Test custom message processor
    message = "Hello"
    result = await websocket_service.process_message(message)
    assert result == f"Custom: {message}"


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
    websocket_service.add_client("client1")
    websocket_service.add_client("client2")

    # Mock broadcasting
    websocket_service.broadcast_message = AsyncMock()
    await websocket_service.broadcast_message("Broadcast Message")

    websocket_service.broadcast_message.assert_called_once_with("Broadcast Message")
