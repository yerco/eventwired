import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from src.services.session_service import SessionService
from src.models.session import Session as SessionModel


@pytest.mark.asyncio
async def test_load_existing_session():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()
    mock_session_data = '{"user_id": 123}'  # Simulated session data from DB
    mock_expiration = datetime.now(timezone.utc) + timedelta(hours=1)  # Valid expiration time
    mock_config_service.get.return_value = 3600  # 1 hour in seconds

    # Step 2: Mock ORM service to return a session when queried
    mock_session = AsyncMock()
    mock_session.session_data = mock_session_data
    mock_session.expires_at = mock_expiration
    mock_orm_service.get.return_value = mock_session

    # Step 3: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 4: Call load_session and assert the result
    result = await session_service.load_session("test-session-id")
    assert result == {"user_id": 123}

    # Step 5: Ensure ORM service was called with correct arguments
    mock_orm_service.get.assert_called_once_with(SessionModel, lookup_value="test-session-id", lookup_column="session_id")


@pytest.mark.asyncio
async def test_load_nonexistent_session():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()

    # Step 2: Mock ORM service to return None (no session found)
    mock_orm_service.get.return_value = None

    # Step 3: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 4: Call load_session and assert the result is an empty dict
    result = await session_service.load_session("nonexistent-session-id")
    assert result == {}

    # Step 5: Ensure ORM service was called with correct arguments
    mock_orm_service.get.assert_called_once_with(SessionModel, lookup_value="nonexistent-session-id", lookup_column="session_id")


@pytest.mark.asyncio
async def test_load_session_no_session_id():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()

    # Step 2: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 3: Call load_session with no session_id and assert the result is an empty dict
    result = await session_service.load_session(None)
    assert result == {}

    # Step 4: Ensure ORM service was not called since no session_id was passed
    mock_orm_service.get_by_column.assert_not_called()


@pytest.mark.asyncio
async def test_load_expired_session():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()
    mock_session_data = '{"user_id": 123}'  # Simulated session data from DB
    mock_expiration = datetime.now(timezone.utc) - timedelta(hours=1)  # Expired session

    # Step 2: Mock ORM service to return an expired session
    mock_session = AsyncMock()
    mock_session.session_data = mock_session_data
    mock_session.expires_at = mock_expiration
    mock_orm_service.get.return_value = mock_session

    # Step 3: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 4: Call load_session and assert the session has been cleared
    result = await session_service.load_session("expired-session-id")
    assert result == {}

    # Step 5: Ensure ORM service was called to delete the expired session
    mock_orm_service.delete.assert_called_once_with(SessionModel, "expired-session-id")


@pytest.mark.asyncio
async def test_save_new_session():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()  # Mock config service
    mock_config_service.get = lambda key, default: 3600  # Return 3600 seconds directly

    # Step 2: Mock the ORM service to return None (no session exists with this session_id)
    mock_orm_service.get.return_value = None

    # Mock config service to return a valid session duration
    mock_config_service.get.return_value = 3600  # 1 hour

    # Step 3: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 4: Call save_session with a new session ID and session data
    session_data = {"user_id": 123}
    await session_service.save_session("new-session-id", session_data)

    # Step 5: Ensure ORM service was called to create a new session
    mock_orm_service.create.assert_called_once()

    # Step 6: Check if the expiration time is correctly set
    args, kwargs = mock_orm_service.create.call_args
    assert "expires_at" in kwargs
    assert kwargs["expires_at"] > datetime.now(timezone.utc)  # Make comparison offset-aware

    # Ensure ORM service did not update (because it's a new session)
    mock_orm_service.update.assert_not_called()


@pytest.mark.asyncio
async def test_save_existing_session():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()  # Mock config service
    mock_config_service.get = lambda key, default: 3600  # Return 3600 seconds directly

    mock_config_service.get.return_value = 3600  # 1 hour

    # Step 2: Mock ORM service to return an existing session
    mock_orm_service.get.return_value = AsyncMock()

    # Step 3: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 4: Call save_session with an existing session ID and updated session data
    session_data = {"user_id": 456}
    await session_service.save_session("existing-session-id", session_data)

    # Step 5: Ensure ORM service was called to update the existing session
    mock_orm_service.update.assert_called_once()

    # Step 6: Check if the expiration time is updated correctly
    args, kwargs = mock_orm_service.update.call_args
    assert "expires_at" in kwargs
    assert kwargs["expires_at"] > datetime.now(timezone.utc)

    # Ensure ORM service did not create a new session
    mock_orm_service.create.assert_not_called()


@pytest.mark.asyncio
async def test_delete_session():
    # Step 1: Mock dependencies
    mock_orm_service = AsyncMock()
    mock_config_service = AsyncMock()  # Mock config service

    # Step 2: Create the session service instance
    session_service = SessionService(orm_service=mock_orm_service, config_service=mock_config_service)

    # Step 3: Call delete_session with a session ID
    await session_service.delete_session("session-id-to-delete")

    # Step 4: Ensure ORM service was called to delete the session using the correct parameter
    mock_orm_service.delete.assert_called_once_with(SessionModel, lookup_value="session-id-to-delete", lookup_column="session_id")
