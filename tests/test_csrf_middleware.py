import pytest
import secrets
from unittest.mock import AsyncMock, mock_open

from src.core.response import Response
from src.core.event_bus import Event
from src.middleware.csrf_middleware import CSRFMiddleware
from src.core.session import Session


@pytest.mark.asyncio
async def test_csrf_middleware_get_request_generates_token_linked_with_session():
    # Step 1: Mock dependencies
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(method='GET'),
        'session': Session('test-session-id', {})
    })
    mock_event_bus = AsyncMock()

    # Step 2: Create the middleware instance
    csrf_middleware = CSRFMiddleware(event_bus=mock_event_bus)

    # Step 3: Call before_request method
    event = await csrf_middleware.before_request(mock_event)

    # Step 4: Check if a CSRF token was generated
    assert 'csrf_token' in event.data['session'].data
    assert isinstance(event.data['session'].data['csrf_token'], str)
    assert len(event.data['session'].data['csrf_token']) == 64  # Check if token length is 32 bytes (64 hex chars)


@pytest.mark.asyncio
async def test_csrf_middleware_get_request_uses_existing_token():
    # Step 1: Mock dependencies
    existing_token = secrets.token_hex(32)
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(method='GET'),
        'session': Session('test-session-id', {'csrf_token': existing_token})
    })
    mock_event_bus = AsyncMock()

    # Step 2: Create the middleware instance
    csrf_middleware = CSRFMiddleware(event_bus=mock_event_bus)

    # Step 3: Call before_request method
    event = await csrf_middleware.before_request(mock_event)

    # Step 4: Ensure the existing CSRF token is not regenerated
    assert event.data['request'].csrf_token == existing_token
    assert event.data['session'].data['csrf_token'] == existing_token


@pytest.mark.asyncio
async def test_csrf_middleware_post_request_valid_token():
    # Step 1: Mock dependencies
    csrf_token = secrets.token_hex(32)
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(method='POST'),
        'session': Session('test-session-id', {'csrf_token': csrf_token})
    })
    mock_event_bus = AsyncMock()
    # Mock form data with the CSRF token
    mock_event.data['request'].form = AsyncMock(return_value={'csrf_token': csrf_token})
    mock_event.data['request'].headers = {'X-CSRF-Token': None}  # Add mock headers if needed

    # Step 2: Create the middleware instance
    csrf_middleware = CSRFMiddleware(event_bus=mock_event_bus)

    # Step 3: Call before_request method for POST request with valid CSRF token
    event = await csrf_middleware.before_request(mock_event)

    # Step 4: No exception should be raised (valid token)
    assert event is not None  # Just verify the middleware did not raise an exception


@pytest.mark.asyncio
async def test_csrf_middleware_post_request_invalid_token_response():
    # Step 1: Mock dependencies
    csrf_token = secrets.token_hex(32)
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(method='POST'),
        'session': Session('test-session-id', {'csrf_token': csrf_token})
    })

    # Mock form data with a different invalid CSRF token and make sure form() is an async mock
    mock_event.data['request'].form = AsyncMock(return_value={'csrf_token': 'invalid-token'})

    # Mock headers to prevent warning
    mock_event.data['request'].headers = {}
    mock_event_bus = AsyncMock()

    # Step 2: Create the middleware instance
    csrf_middleware = CSRFMiddleware(event_bus=mock_event_bus)

    # Step 3: Call before_request method for POST request with invalid CSRF token
    await csrf_middleware.before_request(mock_event)

    # Step 4: Assert that the CSRF failure event was published with a 403 status code
    mock_event_bus.publish.assert_called_once()  # Check that an event was published
    published_event = mock_event_bus.publish.call_args[0][0]  # Retrieve the published event

    # Verify that the published event has the correct name and contains a 403 response
    assert published_event.name == "http.error.403"


@pytest.mark.asyncio
async def test_csrf_middleware_post_request_valid_header_token():
    # Step 1: Mock dependencies
    csrf_token = secrets.token_hex(32)
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(method='POST', headers={'X-CSRF-Token': csrf_token}),
        'session': Session('test-session-id', {'csrf_token': csrf_token})
    })

    # Mock form method even if it's not used in this test, because it's async and might be awaited
    mock_event.data['request'].form = AsyncMock(return_value={})

    mock_event_bus = AsyncMock()

    # Step 2: Create the middleware instance
    csrf_middleware = CSRFMiddleware(event_bus=mock_event_bus)

    # Step 3: Call before_request method with valid CSRF token in header
    event = await csrf_middleware.before_request(mock_event)

    # Step 4: Ensure no exception is raised (valid token from header)
    assert event is not None
