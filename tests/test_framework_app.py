import pytest
from unittest.mock import AsyncMock, patch
from src.core.framework_app import framework_app
from src.event_bus import Event


@pytest.mark.asyncio
async def test_handle_500_error(monkeypatch):
    # Mock the necessary components
    mock_scope = {'type': 'http'}
    mock_receive = AsyncMock()
    mock_send = AsyncMock()

    with patch('src.core.framework_app.handle_http_requests', side_effect=Exception("Forced error")):
        # Mock event bus
        event_bus = AsyncMock()

        # Ensure the event bus is available in the DI container
        monkeypatch.setattr('src.dicontainer.di_container.get', AsyncMock(return_value=event_bus))

        # Call the framework app, which should raise the exception and trigger a 500 error
        await framework_app(mock_scope, mock_receive, mock_send)

        # Check that the 500 error event was published
        actual_event = event_bus.publish.call_args[0][0]
        assert actual_event.name == 'http.error.500'
