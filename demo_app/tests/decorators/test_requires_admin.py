import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.core.dicontainer import di_container
from src.core.context_manager import set_container
from src.core.event_bus import Event
from src.services.session_service import SessionService

from demo_app.decorators.requires_admin import requires_admin
from demo_app.di_setup import setup_container


@pytest.mark.asyncio
async def test_requires_admin_allows_access(monkeypatch):
    called = False

    @requires_admin
    async def mock_controller(event):
        nonlocal called
        called = True
        return "Access granted"

    mock_send = AsyncMock()
    mock_event = Event(name="test_event", data={
        "send": mock_send,
        "request": SimpleNamespace(headers={"cookie": "session_id=abc123"}),
        "session": {}  # Let the decorator use the session service
    })

    # Setup real container so @inject can resolve services
    await setup_container(di_container)
    set_container(di_container)

    # Monkeypatch to simulate an admin user session
    monkeypatch.setattr(SessionService, "load_session", AsyncMock(return_value={"user_id": 1, "is_admin": True}))

    result = await mock_controller(mock_event)

    assert called is True
    assert result == "Access granted"


@pytest.mark.asyncio
async def test_requires_admin_blocks_access(monkeypatch):
    blocked = False

    @requires_admin
    async def mock_controller(event):
        nonlocal blocked
        blocked = True
        return "Should not be called"

    mock_send = AsyncMock()
    mock_event = Event(name="test_event", data={
        "send": mock_send,
        "request": SimpleNamespace(headers={"cookie": "session_id=abc123"}),
        "session": {"user_id": 2, "is_admin": False}
    })

    await setup_container(di_container)
    set_container(di_container)

    await mock_controller(mock_event)

    assert blocked is False
    assert mock_send.call_count == 2

    start_call_args = mock_send.call_args_list[0][0][0]
    body_call_args = mock_send.call_args_list[1][0][0]

    assert start_call_args["type"] == "http.response.start"
    assert body_call_args["type"] == "http.response.body"
    assert b"Unauthorized Access" in body_call_args["body"]
