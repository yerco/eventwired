import pytest
from unittest.mock import AsyncMock, Mock

from src.core.context_manager import set_container
from src.core.dicontainer import DIContainer
from src.core.event_bus import Event

from demo_app.controllers.chat_room_controller import chat_room_controller
from demo_app.di_setup import setup_container


@pytest.mark.asyncio
async def test_chat_room_controller_registration(monkeypatch):
    container = DIContainer()
    await setup_container(container)
    set_container(container)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    websocket_service = await container.get('WebSocketService')
    # Execute the controller
    await chat_room_controller(mock_event, websocket_service=websocket_service)

    # Assert that the controller was registered correctly in the WebSocketService
    assert len(websocket_service.clients) == 1, "Controller was not registered correctly."


@pytest.mark.asyncio
async def test_chat_room_controller_connection(monkeypatch):
    container = DIContainer()
    await setup_container(container)
    set_container(container)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    websocket_service = await container.get('WebSocketService')

    mock_accept_client_connection = AsyncMock()
    monkeypatch.setattr(websocket_service, "accept_client_connection", mock_accept_client_connection)

    # Execute the controller
    await chat_room_controller(mock_event, websocket_service=websocket_service)

    assert len(websocket_service.clients) > 0, "No clients were registered."
    client = websocket_service.clients[0]
    mock_accept_client_connection.assert_awaited_once_with(client)


@pytest.mark.asyncio
async def test_chat_room_controller_message_broadcast(monkeypatch):
    container = DIContainer()
    await setup_container(container)
    set_container(container)

    websocket_service = await container.get('WebSocketService')

    mock_accept_client_connection = AsyncMock()
    monkeypatch.setattr(websocket_service, "broadcast_message", mock_accept_client_connection)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Mock the receive call to simulate a user message and then a disconnect message
    mock_event.data['receive'].side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello World!'},
        {'type': 'websocket.disconnect'}
    ]

    # Execute the controller
    await chat_room_controller(mock_event, websocket_service=websocket_service)

    # Assert that broadcast_message was called with the right content
    websocket_service.broadcast_message.assert_any_call("User: Hello World!")


@pytest.mark.asyncio
async def test_chat_room_controller_disconnection(monkeypatch):
    container = DIContainer()
    await setup_container(container)
    set_container(container)

    websocket_service = await container.get('WebSocketService')

    mock_accept_client_connection = AsyncMock()
    monkeypatch.setattr(websocket_service, "broadcast_message", mock_accept_client_connection)

    # Create a mock event
    mock_event = Event(name="test_event", data={'send': AsyncMock(), 'receive': AsyncMock()})

    # Mock the receive call to simulate a disconnection
    mock_event.data['receive'].side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello'},
        {'type': 'websocket.disconnect'}
    ]

    # Execute the controller
    await chat_room_controller(mock_event, websocket_service=websocket_service)

    # Assert that the WebSocketService does not try to broadcast to disconnected clients
    assert websocket_service.broadcast_message.call_count == 1, "Unexpected broadcasts after disconnect."
