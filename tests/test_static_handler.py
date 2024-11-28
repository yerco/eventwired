import os
import pytest
from unittest.mock import AsyncMock, patch
from src.core.static_handler import StaticFilesHandler

# Directory where we will create temporary static files for testing
STATIC_DIR = "tests/static_test"

# Static handler setup for tests
STATIC_URL_PATH = "/static"
static_handler = StaticFilesHandler(STATIC_DIR, STATIC_URL_PATH, event_bus=AsyncMock())


@pytest.fixture(scope="module", autouse=True)
def setup_static_directory():
    """Setup and teardown for static files directory used in tests."""
    os.makedirs(STATIC_DIR, exist_ok=True)

    # Create some test files
    with open(os.path.join(STATIC_DIR, "test.css"), 'w') as f:
        f.write("body { background-color: #f0f0f0; }")

    with open(os.path.join(STATIC_DIR, "test.js"), 'w') as f:
        f.write("console.log('Test JavaScript file');")

    yield  # This allows the setup to be done before tests and cleanup to happen after

    # Cleanup static directory after tests
    for filename in os.listdir(STATIC_DIR):
        file_path = os.path.join(STATIC_DIR, filename)
        os.remove(file_path)
    os.rmdir(STATIC_DIR)


# Test successful file retrieval
@pytest.mark.asyncio
async def test_static_files_handler_success():
    # Mock the send callable
    send = AsyncMock()

    # Simulate a request to get test.css
    request = type('Request', (), {'path': f"{STATIC_URL_PATH}/test.css"})
    event_data = {
        'request': request,
        'send': send,
    }
    event = type('Event', (), {'data': event_data})

    # Call the handler
    await static_handler.handle(event)

    # Check if the send function was called twice (http.response.start and http.response.body)
    assert send.call_count == 2

    # Check the first send call (http.response.start)
    send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [[b'content-type', b'text/css']],
    })

    # Check the second send call (http.response.body)
    send.assert_any_call({
        'type': 'http.response.body',
        'body': b"body { background-color: #f0f0f0; }",
    })


# Test file not found scenario
@pytest.mark.asyncio
async def test_static_files_handler_file_not_found():
    # Mock the send callable
    send = AsyncMock()

    # Simulate a request to get a non-existent file
    request = type('Request', (), {'path': f"{STATIC_URL_PATH}/non_existent_file.css"})
    event_data = {
        'request': request,
        'send': send,
    }
    event = type('Event', (), {'data': event_data})

    # Call the handler
    await static_handler.handle(event)

    # Check if the send function was called twice (http.response.start and http.response.body)
    assert send.call_count == 2

    # Check the first send call (http.response.start)
    send.assert_any_call({
        'type': 'http.response.start',
        'status': 404,
        'headers': [[b'content-type', b'text/plain']],
    })

    # Check the second send call (http.response.body)
    send.assert_any_call({
        'type': 'http.response.body',
        'body': b'File not found.',
    })


# Test internal server error handling
@pytest.mark.asyncio
async def test_static_files_handler_internal_server_error():
    # Mock the send callable
    send = AsyncMock()

    # Patch aiofiles.open to raise an exception
    with patch("aiofiles.threadpool.sync_open", side_effect=Exception("Test exception")):
        # Simulate a request to get an existing file
        request = type('Request', (), {'path': f"{STATIC_URL_PATH}/test.js"})
        event_data = {
            'request': request,
            'send': send,
        }
        event = type('Event', (), {'data': event_data})

        # Call the handler
        await static_handler.handle(event)

        # Check if the send function was called twice (http.response.start and http.response.body)
        assert send.call_count == 2

        # Check the first send call (http.response.start)
        send.assert_any_call({
            'type': 'http.response.start',
            'status': 500,
            'headers': [[b'content-type', b'text/plain']],
        })

        # Check the second send call (http.response.body)
        send.assert_any_call({
            'type': 'http.response.body',
            'body': b'Internal server error.',
        })
