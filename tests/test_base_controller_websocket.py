import pytest
from unittest.mock import AsyncMock

from src.controllers.base_controller import BaseController
from src.event_bus import Event


@pytest.mark.asyncio
async def test_websocket_accept():
    # Mock send callable to capture sent messages
    mock_send = AsyncMock()

    # Create an Event with the mock send
    event = Event(name='test_websocket', data={'send': mock_send})

    # Initialize the controller
    controller = BaseController(event)

    # Test WebSocket acceptance
    await controller.accept_websocket()

    # Check that the send method was called with websocket.accept
    mock_send.assert_called_once_with({
        'type': 'websocket.accept'
    })


@pytest.mark.asyncio
async def test_websocket_receive_message():
    # Mock receive callable to simulate WebSocket messages
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello WebSocket!'}
    ]

    # Create an Event with the mock receive and send
    event = Event(name='test_websocket', data={'receive': mock_receive, 'send': AsyncMock()})

    # Initialize the controller
    controller = BaseController(event)

    # Test receiving a WebSocket message
    message = await controller.receive_websocket_message()

    assert message == 'Hello WebSocket!'


@pytest.mark.asyncio
async def test_websocket_send_message():
    # Mock send callable to capture sent messages
    mock_send = AsyncMock()

    # Create an Event with the mock send
    event = Event(name='test_websocket', data={'send': mock_send})

    # Initialize the controller
    controller = BaseController(event)

    # Test sending a WebSocket message
    await controller.send_websocket_message('Test Message')

    # Check that the send method was called with the correct message
    mock_send.assert_called_once_with({
        'type': 'websocket.send',
        'text': 'Test Message'
    })


@pytest.mark.asyncio
async def test_websocket_close():
    # Mock send callable to capture sent messages
    mock_send = AsyncMock()

    # Create an Event with the mock send
    event = Event(name='test_websocket', data={'send': mock_send})

    # Initialize the controller
    controller = BaseController(event)

    # Test closing the WebSocket connection
    await controller.close_websocket()

    # Check that the send method was called with websocket.close
    mock_send.assert_called_once_with({
        'type': 'websocket.close',
        'code': 1000  # Normal closure
    })
