import pytest
from unittest.mock import AsyncMock, Mock

from src.event_bus import Event

from demo_app.controllers.hello_controller import hello_controller
from demo_app.di_setup import di_container


@pytest.mark.asyncio
async def test_hello_controller(monkeypatch):
    # Mock dependencies
    mock_orm_service = AsyncMock()
    mock_template_service = Mock()
    mock_send = AsyncMock()
    mock_user = AsyncMock()
    mock_user.username = "test_user"  # Simulate a User object with a username

    # Mock the DI container to return the ORMService and TemplateService
    async def mock_get(service_name):
        services = {
            'ORMService': mock_orm_service,
            'TemplateService': mock_template_service,
        }
        return services[service_name]

    monkeypatch.setattr(di_container, 'get', mock_get)

    # Mock ORMService to return a list of users
    mock_orm_service.all.return_value = [mock_user]

    # Mock TemplateService to return the expected rendered content
    expected_response_message = "Hello from the demo app! Users: test_user"
    mock_template_service.render_template.return_value = expected_response_message

    # Create a mock event with a send function
    event = Event(name="http.request.received", data={"send": mock_send})

    # Call the hello_controller function
    await hello_controller(event)

    # Prepare the expected response message
    expected_response_message = "Hello from the demo app! Users: test_user"

    # Assert that send_text is called with the expected message
    assert "response" in event.data  # Ensure that the response was added to the event
    response = event.data['response']

    assert response.content == expected_response_message
    assert response.status_code == 200
    assert response.content_type == "text/html"

    # Ensure that the send function is called with the correct data
    await response.send(mock_send)

    mock_send.assert_any_call({
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"text/html")],
    })
    mock_send.assert_any_call({
        "type": "http.response.body",
        "body": expected_response_message.encode(),
    })
