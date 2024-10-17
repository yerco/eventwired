import pytest
from unittest.mock import AsyncMock

from src.core.lifecycle import handle_lifespan_events


@pytest.mark.asyncio
async def test_handle_lifespan_events_startup():
    # Mock receive to simulate a lifespan startup message
    receive = AsyncMock()
    receive.side_effect = [{'type': 'lifespan.startup'}, {'type': 'lifespan.shutdown'}]

    # Mock send to capture the output
    send = AsyncMock()

    scope = {'type': 'lifespan'}

    # Run the lifespan event handler
    await handle_lifespan_events(scope, receive, send)

    # Check that the startup message was handled and send was called with the correct output
    send.assert_any_call({'type': 'lifespan.startup.complete'})
    send.assert_any_call({'type': 'lifespan.shutdown.complete'})


@pytest.mark.asyncio
async def test_handle_lifespan_events_shutdown():
    # Mock receive to simulate a shutdown message
    receive = AsyncMock()
    receive.side_effect = [{'type': 'lifespan.shutdown'}]

    # Mock send to capture the output
    send = AsyncMock()

    scope = {'type': 'lifespan'}

    # Run the lifespan event handler
    await handle_lifespan_events(scope, receive, send)

    # Check that the shutdown message was handled correctly
    send.assert_called_once_with({'type': 'lifespan.shutdown.complete'})


@pytest.mark.asyncio
async def test_handle_lifespan_events_unsupported_message():
    # Mock receive to simulate an unsupported message type
    receive = AsyncMock()
    receive.side_effect = [{'type': 'unsupported.message'}, {'type': 'lifespan.shutdown'}]

    # Mock send to capture the output
    send = AsyncMock()

    scope = {'type': 'lifespan'}

    # Run the lifespan event handler
    await handle_lifespan_events(scope, receive, send)

    # Check that the unsupported message triggered the print and send the correct response
    send.assert_any_call({'type': 'lifespan.shutdown.complete'})
    send.assert_called_with({'type': 'lifespan.shutdown.complete'})


@pytest.mark.asyncio
async def test_handle_lifespan_events_exception_handling(capfd):
    # Mock receive to raise an exception
    receive = AsyncMock()
    receive.side_effect = Exception("Test exception")

    # Mock send to capture the output
    send = AsyncMock()

    scope = {'type': 'lifespan'}

    # Run the lifespan event handler
    await handle_lifespan_events(scope, receive, send)

    # Check that the exception was caught and handled correctly
    send.assert_called_with({'type': 'lifespan.shutdown.complete'})

    # Capture and verify the printed output
    captured = capfd.readouterr()
    assert "Error during lifespan handling: Test exception" in captured.out
