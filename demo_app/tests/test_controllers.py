import pytest
from unittest.mock import AsyncMock

from src.event_bus import Event

from demo_app.controllers.hello_controller import hello_controller
from demo_app.di_setup import di_container


@pytest.mark.asyncio
async def test_hello_controller():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_send = AsyncMock()
    mock_user = AsyncMock()
    mock_user.username = "test_user"  # Simulate a User object with a username

    # Step 2: Mock the DI container to return the ORMService
    di_container.get = AsyncMock(return_value=mock_orm_service)

    # Step 3: Mock ORMService to return a list of users
    mock_orm_service.all.return_value = [mock_user]

    # Step 4: Create a mock event with a send function
    event = Event(name="http.request.received", data={"send": mock_send})

    # Step 5: Call the hello_controller function
    await hello_controller(event)

    # Step 6: Prepare the expected response message
    expected_response_message = "Hello from the demo app! Users: test_user"

    # Step 7: Assert that send_text is called with the expected message
    assert "response" in event.data  # Ensure that the response was added to the event
    response = event.data['response']
    assert response.content == expected_response_message
    assert response.status_code == 200
    assert response.content_type == "text/plain"

    # Step 8: Ensure that the send function is called with the correct data
    await response.send(mock_send)

    mock_send.assert_any_call({
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"text/plain")],
    })
    mock_send.assert_any_call({
        "type": "http.response.body",
        "body": expected_response_message.encode(),
    })
