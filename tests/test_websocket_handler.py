import pytest
from unittest.mock import AsyncMock
from src.services.websocket_handler import WebSocketHandler


@pytest.mark.asyncio
async def test_accept_websocket():
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    websocket_service = WebSocketHandler(mock_send, mock_receive)
    await websocket_service.accept_websocket()

    mock_send.assert_called_once_with({
        'type': 'websocket.accept'
    })


@pytest.mark.asyncio
async def test_receive_websocket_message():
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello WebSocket!'}
    ]
    mock_send = AsyncMock()

    websocket_client_handler = WebSocketHandler(mock_send, mock_receive)
    message = await websocket_client_handler.receive_websocket_message()

    assert message == "Hello WebSocket!"


@pytest.mark.asyncio
async def test_websocket_message_with_timeout():
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello WebSocket!'}
    ]
    mock_send = AsyncMock()

    websocket_client_handler = WebSocketHandler(mock_send, mock_receive)
    message = await websocket_client_handler.receive_websocket_message_with_timeout()

    assert message == "Hello WebSocket!"


@pytest.mark.asyncio
async def test_send_websocket_message():
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    websocket_service = WebSocketHandler(mock_send, mock_receive)
    await websocket_service.send_websocket_message("Test Message")

    mock_send.assert_called_once_with({
        'type': 'websocket.send',
        'text': 'Test Message'
    })


@pytest.mark.asyncio
async def test_close_websocket():
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    websocket_service = WebSocketHandler(mock_send, mock_receive)
    await websocket_service.close_websocket()

    mock_send.assert_called_once_with({
        'type': 'websocket.close',
        'code': 1000
    })


@pytest.mark.asyncio
async def test_receive_message():
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello WebSocket!'}
    ]
    mock_send = AsyncMock()

    websocket_client_handler = WebSocketHandler(mock_send, mock_receive)
    message = await websocket_client_handler.receive_message(mock_receive)

    assert message == "Hello WebSocket!"


@pytest.mark.asyncio
async def test_send_message():
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    websocket_service = WebSocketHandler(mock_send, mock_receive)
    await websocket_service.send_message(mock_send, "Test Message")

    mock_send.assert_called_once_with({
        'type': 'websocket.send',
        'text': 'Test Message'
    })

