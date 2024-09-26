import pytest
from unittest.mock import AsyncMock, patch

from src.event_bus import Event

from demo_app.controllers.websocket_controller import websocket_controller


@pytest.mark.asyncio
async def test_websocket_controller_receive_and_send():
    # Mock send and receive callables
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate an incoming WebSocket message and a disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'Hello Server!'},
        {'type': 'websocket.disconnect'}  # Simulate disconnection after receiving message
    ]

    # Create the event with mock receive and send
    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Patch the WebSocketService to mock process_message method
    with patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock) as mock_get:
        # Mock the WebSocketService and its process_message method
        mock_websocket_service = AsyncMock()
        mock_websocket_service.process_message.return_value = 'Processed: Hello Server!'
        mock_get.return_value = mock_websocket_service

        # Call the controller
        await websocket_controller(event)

        # Verify that the WebSocket was accepted
        mock_send.assert_any_call({
            'type': 'websocket.accept'
        })

        # Verify that the message was processed and echoed back
        mock_send.assert_any_call({
            'type': 'websocket.send',
            'text': 'Processed: Hello Server!'
        })

        # Verify that the WebSocket was closed after disconnect
        mock_send.assert_any_call({
            'type': 'websocket.send',
            'text': 'Server is shutting down. Please reconnect later.'
        })
        mock_send.assert_any_call({
            'type': 'websocket.close',
            'code': 1000
        })


@pytest.mark.asyncio
async def test_websocket_controller_custom_processing():
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate custom message being sent and processed
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'CustomMessage!'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Patch the WebSocketService to mock a custom process_message response
    with patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock) as mock_get:
        mock_websocket_service = AsyncMock()
        mock_websocket_service.process_message.return_value = 'Processed: CustomMessage!'
        mock_get.return_value = mock_websocket_service

        # Call the controller
        await websocket_controller(event)

        # Verify custom message processing and send back
        mock_send.assert_any_call({
            'type': 'websocket.send',
            'text': 'Processed: CustomMessage!'
        })


@pytest.mark.asyncio
async def test_websocket_controller_ping_pong():
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate ping message and disconnection
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'ping'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Patch the WebSocketService (not needed for ping)
    with patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock):
        # Call the controller
        await websocket_controller(event)

        # Verify the WebSocket responded with pong
        mock_send.assert_any_call({
            'type': 'websocket.send',
            'text': 'pong'
        })


@pytest.mark.asyncio
async def test_websocket_controller_disconnect():
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate the client sending 'disconnect'
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'disconnect'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Patch the WebSocketService (not needed for disconnect)
    with patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock):
        # Call the controller
        await websocket_controller(event)

        # Verify that the WebSocket was closed after 'disconnect'
        mock_send.assert_any_call({
            'type': 'websocket.close',
            'code': 1000
        })


@pytest.mark.asyncio
async def test_websocket_controller_exit_message():
    mock_send = AsyncMock()
    mock_receive = AsyncMock()

    # Simulate the client sending 'exit'
    mock_receive.side_effect = [
        {'type': 'websocket.receive', 'text': 'exit'},
        {'type': 'websocket.disconnect'}
    ]

    event = Event(name="websocket_event", data={"receive": mock_receive, "send": mock_send})

    # Patch the WebSocketService (not needed for 'exit')
    with patch('demo_app.di_setup.di_container.get', new_callable=AsyncMock):
        # Call the controller
        await websocket_controller(event)

        # Verify that the WebSocket was closed after 'exit'
        mock_send.assert_any_call({
            'type': 'websocket.send',
            'text': 'Server is shutting down. Please reconnect later.'
        })
        mock_send.assert_any_call({
            'type': 'websocket.close',
            'code': 1000
        })
