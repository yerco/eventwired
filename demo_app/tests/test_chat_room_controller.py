import pytest
from unittest.mock import AsyncMock, Mock
from demo_app.controllers.chat_room_controller import chat_room_controller
from src.core.event_bus import Event
from src.services.websocket_service import WebSocketService


@pytest.mark.asyncio
async def test_chat_room_controller_registration(monkeypatch):
    # Mock WebSocketService
    mock_websocket_service = WebSocketService()
    mock_websocket_service.register_client = Mock()
    mock_websocket_service.accept_client_connection = AsyncMock()

    # Mock DI container to provide WebSocketService
    async def mock_get(service_name):
        if service_name == 'WebSocketService':
            return mock_websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', mock_get)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Execute the controller
    await chat_room_controller(mock_event)

    # Assert that the controller was registered correctly in the WebSocketService
    assert mock_websocket_service.register_client.called, "Controller was not registered in WebSocketService."


@pytest.mark.asyncio
async def test_chat_room_controller_connection(monkeypatch):
    # Mock WebSocketService
    mock_websocket_service = WebSocketService()
    mock_websocket_service.accept_client_connection = AsyncMock()

    # Mock DI container to provide WebSocketService
    async def mock_get(service_name):
        if service_name == 'WebSocketService':
            return mock_websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', mock_get)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Execute the controller
    await chat_room_controller(mock_event)

    # Assert that the connection was accepted
    mock_websocket_service.accept_client_connection.assert_called_once()


@pytest.mark.asyncio
async def test_chat_room_controller_message_broadcast(monkeypatch):
    # Mock WebSocketService
    mock_websocket_service = WebSocketService()
    mock_websocket_service.broadcast_message = AsyncMock()

    # Mock DI container to provide WebSocketService
    async def mock_get(service_name):
        if service_name == 'WebSocketService':
            return mock_websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', mock_get)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Mock the receive call to simulate a user message and then a disconnect message
    mock_event.data['receive'].side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello World!'},
        {'type': 'websocket.disconnect'}
    ]

    # Execute the controller
    await chat_room_controller(mock_event)

    # Assert that broadcast_message was called with the right content
    mock_websocket_service.broadcast_message.assert_any_call("User: Hello World!")


@pytest.mark.asyncio
async def test_chat_room_controller_disconnection(monkeypatch):
    # Mock WebSocketService
    mock_websocket_service = WebSocketService()
    mock_websocket_service.broadcast_message = AsyncMock()

    # Mock DI container to provide WebSocketService
    async def mock_get(service_name):
        if service_name == 'WebSocketService':
            return mock_websocket_service
    monkeypatch.setattr('demo_app.di_setup.di_container.get', mock_get)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Mock the receive call to simulate a disconnection
    mock_event.data['receive'].side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello'},
        {'type': 'websocket.disconnect'}
    ]

    # Execute the controller
    await chat_room_controller(mock_event)

    # Assert that the WebSocketService does not try to broadcast to disconnected clients
    assert mock_websocket_service.broadcast_message.call_count == 1, "Unexpected broadcasts after disconnect."
