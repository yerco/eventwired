import pytest
from unittest.mock import AsyncMock
from src.core.event_bus import Event
from src.middleware.session_middleware import SessionMiddleware
from src.core.session import Session


@pytest.mark.asyncio
async def test_session_middleware_before_request():
    # Step 1: Mock dependencies
    mock_session_service = AsyncMock()
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(cookies={'session_id': 'test-session-id'})
    })

    # Step 2: Mock the session service to return some session data
    mock_session_service.load_session.return_value = {'user_id': 123}

    # Step 3: Create the middleware instance
    middleware = SessionMiddleware(session_service=mock_session_service)

    # Step 4: Call the before_request method
    event = await middleware.before_request(mock_event)

    # Step 5: Assert that session was loaded
    mock_session_service.load_session.assert_called_once_with('test-session-id')

    # Step 6: Assert that session data is attached to the event
    session = event.data['session']
    assert isinstance(session, Session)
    assert session.data == {'user_id': 123}
    assert session.session_id == 'test-session-id'


@pytest.mark.asyncio
async def test_session_middleware_after_request_modified_session():
    # Step 1: Mock dependencies
    mock_session_service = AsyncMock()
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(cookies={'session_id': 'test-session-id'}),
        'session': Session('test-session-id', {'user_id': 123}),
        'set_session_id': 'test-session-id'  # Ensure set_session_id is in event data
    })

    # Step 2: Simulate session modification
    mock_event.data['session'].set('key', 'value')

    # Step 3: Create the middleware instance
    middleware = SessionMiddleware(session_service=mock_session_service)

    # Step 4: Call the after_request method
    await middleware.after_request(mock_event)

    # Step 5: Assert that the session service was called to save the session
    mock_session_service.save_session.assert_called_once_with('test-session-id', {'user_id': 123, 'key': 'value'})

    # Step 6: Assert that Set-Cookie is in response headers (update to match middleware logic)
    assert 'response_headers' in mock_event.data
    assert ('Set-Cookie', 'session_id=test-session-id; Path=/; HttpOnly; Secure; SameSite=Strict') in mock_event.data['response_headers']


@pytest.mark.asyncio
async def test_session_middleware_after_request_unmodified_session():
    # Step 1: Mock dependencies
    mock_session_service = AsyncMock()
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(cookies={'session_id': 'test-session-id'}),
        'session': Session('test-session-id', {'user_id': 123})
    })

    # Step 2: Create the middleware instance
    middleware = SessionMiddleware(session_service=mock_session_service)

    # Step 3: Call the after_request method
    await middleware.after_request(mock_event)

    # Step 4: Assert that the session service was NOT called to save the session
    mock_session_service.save_session.assert_not_called()

    # Step 5: Assert that no Set-Cookie header was added
    assert 'response_headers' not in mock_event.data


@pytest.mark.asyncio
async def test_session_middleware_before_request_no_session_id():
    # Step 1: Mock dependencies
    mock_session_service = AsyncMock()
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(cookies={}),  # No session_id in cookies
    })

    # Step 2: Create the middleware instance
    middleware = SessionMiddleware(session_service=mock_session_service)

    # Step 3: Call the before_request method
    updated_event = await middleware.before_request(mock_event)

    # Step 4: Assert that a session was created and a new session_id was generated
    session = updated_event.data['session']
    assert session.session_id is not None  # A new session_id should be generated
    assert isinstance(session.session_id, str)  # Ensure it's a string

    # Step 5: Assert that no session was loaded from the session service, since no session_id was present
    mock_session_service.load_session.assert_not_called()

    # Ensure the newly generated session is properly set in the event
    assert 'set_session_id' in updated_event.data
    assert updated_event.data['set_session_id'] == session.session_id


@pytest.mark.asyncio
async def test_session_expiration():
    mock_session_service = AsyncMock()
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(cookies={'session_id': 'expired-session-id'})
    })

    # Mock expired session
    mock_session_service.load_session.return_value = {}
    mock_session_service.is_expired.return_value = True

    middleware = SessionMiddleware(session_service=mock_session_service)
    event = await middleware.before_request(mock_event)

    # Ensure a new session is created if the previous one was expired
    session = event.data['session']
    assert session.session_id != 'expired-session-id'  # New session ID should be generated
    assert isinstance(session.session_id, str)

    # Ensure the expired session is deleted
    mock_session_service.delete_session.assert_called_once_with('expired-session-id')


@pytest.mark.asyncio
async def test_session_middleware_logout():
    # Step 1: Mock dependencies
    mock_session_service = AsyncMock()
    mock_event = Event(name='http.request.received', data={
        'request': AsyncMock(cookies={'session_id': 'test-session-id'}),
        'session': Session('test-session-id', {'user_id': 123})
    })

    # Step 2: Mock the logout controller
    async def mock_logout_controller(event):
        session = event.data.get('session')
        if session:
            await mock_session_service.delete_session(session.session_id)

    # Step 3: Call the logout logic
    middleware = SessionMiddleware(session_service=mock_session_service)
    await middleware.before_request(mock_event)
    await mock_logout_controller(mock_event)

    # Step 4: Ensure the session was deleted
    mock_session_service.delete_session.assert_called_once_with('test-session-id')
