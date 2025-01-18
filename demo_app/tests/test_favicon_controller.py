import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock
from demo_app.controllers.favicon_controller import favicon_controller
from demo_app.di_setup import setup_container
from src.core.context_manager import set_container
from src.core.dicontainer import DIContainer
from src.core.event_bus import Event


@pytest.mark.asyncio
async def test_favicon_controller_file_found():
    container = DIContainer()
    await setup_container(container)
    set_container(container)
    mock_event = Event(name="test_event", data={"send": AsyncMock()})
    mock_config_service = MagicMock()

    # Create a temporary directory and file to simulate the favicon
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_config_service.get.return_value = temp_dir
        favicon_path = os.path.join(temp_dir, "favicon.ico")

        with open(favicon_path, "wb") as f:
            f.write(b"Mock favicon content")

        # Call the controller
        await favicon_controller(mock_event, mock_config_service)

        # Validate the response
        response = mock_event.data['response']
        assert response.content == b"Mock favicon content"
        assert response.status_code == 200
        assert response.content_type == "image/x-icon"


@pytest.mark.asyncio
async def test_favicon_controller_file_not_found():
    container = DIContainer()
    await setup_container(container)
    set_container(container)
    mock_event = Event(name="test_event", data={"send": AsyncMock()})
    mock_config_service = MagicMock()
    mock_config_service.get.return_value = "/mock/template/dir"

    await favicon_controller(mock_event, mock_config_service)
    response = mock_event.data['response']
    assert response.content == "Favicon not found"
    assert response.status_code == 404
