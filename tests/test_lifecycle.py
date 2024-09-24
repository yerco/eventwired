import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.lifecycle import startup, shutdown, handle_lifespan_events


# Tests for the startup function
@pytest.mark.asyncio
async def test_startup_success():
    # Mock services and DI container
    mock_orm_service = AsyncMock()
    mock_routing_service = AsyncMock()
    mock_di_container = AsyncMock()

    # Configure the DI container to return mock services
    mock_di_container.get.side_effect = lambda service_name: {
        'ORMService': mock_orm_service,
        'RoutingService': mock_routing_service,
    }.get(service_name)

    # Call startup without a user callback
    await startup(mock_di_container)

    # Assert ORMService and RoutingService methods were called
    mock_orm_service.init.assert_called_once()
    mock_orm_service.create_tables.assert_called_once()
    mock_routing_service.start_routing.assert_called_once()


@pytest.mark.asyncio
async def test_startup_with_user_callback():
    # Mock DI container and services
    mock_orm_service = AsyncMock()
    mock_routing_service = AsyncMock()
    mock_di_container = AsyncMock()
    mock_di_container.get.side_effect = lambda service_name: {
        'ORMService': mock_orm_service,
        'RoutingService': mock_routing_service,
    }.get(service_name)

    # User-defined startup callback
    user_startup_callback = AsyncMock()

    # Call the startup function with user callback
    await startup(mock_di_container, user_startup_callback=user_startup_callback)

    # Assert ORMService and RoutingService were initialized and started
    mock_orm_service.init.assert_called_once()
    mock_orm_service.create_tables.assert_called_once()
    mock_routing_service.start_routing.assert_called_once()

    # Assert user callback was called
    user_startup_callback.assert_called_once_with(mock_di_container)


@pytest.mark.asyncio
async def test_startup_routing_service_not_found():
    # Mock DI container with ORMService but without RoutingService
    mock_orm_service = AsyncMock()
    mock_di_container = AsyncMock()

    # Set up the DI container to return ORMService, but return None for RoutingService
    async def mock_get(service_name):
        if service_name == 'ORMService':
            return mock_orm_service
        elif service_name == 'RoutingService':
            return None  # Simulate missing RoutingService

    mock_di_container.get.side_effect = mock_get

    # Expect a ValueError when RoutingService is not found
    with pytest.raises(ValueError, match="RoutingService is not configured properly"):
        await startup(mock_di_container)


@pytest.mark.asyncio
async def test_shutdown_with_cleanup():
    # Mock DI container and ORMService
    mock_orm_service = AsyncMock()
    mock_di_container = MagicMock()
    mock_di_container.get = AsyncMock(return_value=mock_orm_service)

    # Call the shutdown function
    await shutdown(mock_di_container)

    # Assert ORMService cleanup was called
    mock_orm_service.cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_orm_cleanup_failure():
    # Mock DI container and ORMService
    mock_orm_service = AsyncMock()
    mock_orm_service.cleanup.side_effect = Exception("Cleanup failed")
    mock_di_container = MagicMock()
    mock_di_container.get = AsyncMock(return_value=mock_orm_service)

    # Call the shutdown function and expect no exception
    await shutdown(mock_di_container)

    # Assert ORMService cleanup was called and exception was printed
    mock_orm_service.cleanup.assert_called_once()


# Tests for the handle_lifespan_events function
@pytest.mark.asyncio
async def test_handle_lifespan_events_startup():
    # Mock DI container, receive, send, and request
    mock_receive = AsyncMock()
    mock_receive.side_effect = [{'type': 'lifespan.startup'}, {'type': 'lifespan.shutdown'}]
    mock_send = AsyncMock()
    mock_request = AsyncMock()
    mock_di_container = AsyncMock()

    # Patch startup and shutdown
    with patch('src.core.lifecycle.startup', new=AsyncMock()) as mock_startup, \
            patch('src.core.lifecycle.shutdown', new=AsyncMock()) as mock_shutdown:

        # Call handle_lifespan_events
        await handle_lifespan_events({'type': 'lifespan'}, mock_receive, mock_send, mock_request, mock_di_container)

        # Assert that startup and shutdown were called
        mock_startup.assert_called_once_with(mock_di_container, None)
        mock_shutdown.assert_called_once_with(mock_di_container)

        # Assert that send was called with the correct messages
        mock_send.assert_any_call({'type': 'lifespan.startup.complete'})
        mock_send.assert_any_call({'type': 'lifespan.shutdown.complete'})


@pytest.mark.asyncio
async def test_handle_lifespan_startup():
    # Mock DI container, send/receive functions, and request
    mock_orm_service = AsyncMock()
    mock_routing_service = AsyncMock()
    mock_send = AsyncMock()
    mock_receive = AsyncMock(side_effect=[
        {'type': 'lifespan.startup'},
        {'type': 'lifespan.shutdown'}
    ])

    mock_di_container = AsyncMock()
    mock_di_container.get.side_effect = lambda service_name: {
        'ORMService': mock_orm_service,
        'RoutingService': mock_routing_service,
    }.get(service_name)

    # Call the handle_lifespan_events function
    request = MagicMock()
    await handle_lifespan_events(
        scope={'type': 'lifespan'},
        receive=mock_receive,
        send=mock_send,
        request=request,
        di_container=mock_di_container
    )

    # Assert ORMService and RoutingService were initialized and started
    mock_orm_service.init.assert_called_once()
    mock_orm_service.create_tables.assert_called_once()
    mock_routing_service.start_routing.assert_called_once()

    # Assert that startup and shutdown messages were sent
    mock_send.assert_any_call({'type': 'lifespan.startup.complete'})
    mock_send.assert_any_call({'type': 'lifespan.shutdown.complete'})


@pytest.mark.asyncio
async def test_handle_lifespan_shutdown():
    # Mock DI container, send/receive functions
    di_container = MagicMock()
    send = AsyncMock()
    receive = AsyncMock(side_effect=[
        {'type': 'lifespan.shutdown'}  # Directly start with shutdown
    ])

    orm_service = AsyncMock()
    di_container.get = AsyncMock(side_effect=lambda service: orm_service if service == 'ORMService' else None)

    # Mock request
    request = MagicMock()

    # Call the handle_lifespan_events function (simulate shutdown lifecycle event)
    await handle_lifespan_events(
        scope={'type': 'lifespan'},
        receive=receive,
        send=send,
        request=request,
        di_container=di_container
    )

    # Assert that shutdown messages were sent and ORMService cleanup was called
    orm_service.cleanup.assert_called_once()
    send.assert_any_call({'type': 'lifespan.shutdown.complete'})
