import pytest
from unittest.mock import AsyncMock
from src.middleware.cors_middleware import CORSMiddleware
from src.core.event_bus import Event
from src.core.response import Response
from src.services.config_service import ConfigService
from src.core.request import Request


# Helper function to create a request scope with headers
def create_scope(method, path, headers=None):
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
    }


@pytest.fixture
def config_service():
    mock_config = ConfigService()
    mock_config.get = lambda key, default: {
        'CORS_ALLOWED_ORIGINS': ["http://localhost:5173"],
        'CORS_ALLOWED_METHODS': ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        'CORS_ALLOWED_HEADERS': ["Content-Type", "Authorization", "X-CSRFToken"],
        'CORS_ALLOW_CREDENTIALS': True
    }.get(key, default)
    return mock_config


@pytest.fixture
def cors_middleware(config_service):
    return CORSMiddleware(config_service=config_service)


# Test GET request with allowed origin sets correct CORS headers
@pytest.mark.asyncio
async def test_cors_allowed_origin_get_request(cors_middleware):
    scope = create_scope("GET", "/", headers={"Origin": "http://localhost:5173"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    updated_event = await cors_middleware.before_request(event)
    assert "Access-Control-Allow-Origin" in updated_event.data['add_headers']
    assert updated_event.data['add_headers']["Access-Control-Allow-Origin"] == "http://localhost:5173"


# Test GET request with disallowed origin does not set CORS headers
@pytest.mark.asyncio
async def test_cors_disallowed_origin_get_request(cors_middleware):
    scope = create_scope("GET", "/", headers={"Origin": "http://disallowed.com"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    updated_event = await cors_middleware.before_request(event)

    # Check that 'add_headers' is not defined in the event data when the origin is disallowed
    assert 'add_headers' not in updated_event.data


# Helper function to convert headers to a dictionary
def headers_to_dict(headers):
    return {k.decode(): v.decode() for k, v in headers}

# Test OPTIONS preflight request returns 204 response with CORS headers.
@pytest.mark.asyncio
async def test_cors_preflight_options_request(cors_middleware):
    scope = create_scope("OPTIONS", "/", headers={"Origin": "http://localhost:5173"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    updated_event = await cors_middleware.before_request(event)
    response = updated_event.data['response']

    assert response.status_code == 204

    # Convert headers to dictionary for easier assertions
    headers_dict = headers_to_dict(response.headers)

    # Assert individual headers
    assert headers_dict["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert headers_dict["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE, OPTIONS"
    assert headers_dict["Access-Control-Allow-Headers"] == "Content-Type, Authorization, X-CSRFToken"


# Test that allow_credentials=True adds Access-Control-Allow-Credentials header.
@pytest.mark.asyncio
async def test_cors_allow_credentials(cors_middleware):
    scope = create_scope("GET", "/", headers={"Origin": "http://localhost:5173"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    await cors_middleware.before_request(event)
    response = Response(content="Hello, World", status_code=200)
    event.data['response'] = response
    await cors_middleware.after_request(event)
    headers_dict = headers_to_dict(response.headers)
    assert headers_dict["Access-Control-Allow-Credentials"] == "true"


# Test that after_request adds CORS headers to the response
@pytest.mark.asyncio
async def test_after_request_applies_cors_headers(cors_middleware):
    scope = create_scope("GET", "/", headers={"Origin": "http://localhost:5173"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    await cors_middleware.before_request(event)
    response = Response(content="Hello, World", status_code=200)
    event.data['response'] = response
    await cors_middleware.after_request(event)

    headers_dict = headers_to_dict(response.headers)

    # Ensure CORS headers are set on response
    assert headers_dict["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert headers_dict["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE, OPTIONS"


# Test OPTIONS preflight request without origin does not add CORS headers.
@pytest.mark.asyncio
async def test_cors_preflight_no_origin(cors_middleware):
    scope = create_scope("OPTIONS", "/")
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    updated_event = await cors_middleware.before_request(event)

    # Check that 'response' is not added to the event data
    assert 'response' not in updated_event.data
    assert 'add_headers' not in updated_event.data


# Test that unsupported methods (e.g., PATCH) do not add CORS headers.
@pytest.mark.asyncio
async def test_invalid_method_does_not_add_headers(cors_middleware):
    scope = create_scope("PATCH", "/", headers={"Origin": "http://localhost:5173"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    updated_event = await cors_middleware.before_request(event)
    assert "Access-Control-Allow-Origin" not in updated_event.data.get('add_headers', {})


# Test CORS middleware allows multiple origins and correctly sets the header.
@pytest.mark.asyncio
async def test_cors_headers_with_multiple_origins(cors_middleware):
    cors_middleware.allowed_origins = ["http://localhost:5173", "http://another-origin.com"]
    cors_middleware.origin_patterns = cors_middleware._generate_origin_patterns(cors_middleware.allowed_origins)  # Manually regenerate patterns

    scope = create_scope("GET", "/", headers={"Origin": "http://another-origin.com"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    await cors_middleware.before_request(event)
    response = Response(content="Hello, World", status_code=200)
    event.data['response'] = response
    await cors_middleware.after_request(event)
    headers_dict = headers_to_dict(response.headers)
    assert headers_dict["Access-Control-Allow-Origin"] == "http://another-origin.com"


@pytest.fixture
def cors_middleware_all(config_service):
    # Allow all origins with wildcard "*"
    config_service.get = lambda key, default: {"CORS_ALLOWED_ORIGINS": ["*"],
                                               "CORS_ALLOWED_METHODS": ["GET", "POST", "OPTIONS"],
                                               "CORS_ALLOWED_HEADERS": ["Content-Type", "Authorization"],
                                               "CORS_ALLOW_CREDENTIALS": True}.get(key, default)
    return CORSMiddleware(config_service=config_service)


# Test that requests from any origin are allowed when "*" is in allowed_origins
@pytest.mark.asyncio
async def test_cors_wildcard_origin_allows_any_origin(cors_middleware_all):
    # Define a scope with an arbitrary origin
    scope = create_scope("GET", "/", headers={"Origin": "http://example.com"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    # Call before_request to process the event
    updated_event = await cors_middleware_all.before_request(event)
    # Ensure add_headers contains the "Access-Control-Allow-Origin" set to "*"
    assert updated_event.data['add_headers']["Access-Control-Allow-Origin"] == "*"


# Test preflight (OPTIONS) request with wildcard origin
@pytest.mark.asyncio
async def test_cors_preflight_with_wildcard(cors_middleware_all):
    # Define a scope with OPTIONS method and an arbitrary origin
    scope = create_scope("OPTIONS", "/", headers={"Origin": "http://another-origin.com"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    # Call before_request to handle preflight request
    updated_event = await cors_middleware_all.before_request(event)
    response = updated_event.data['response']

    # Check that the response has a 204 status code
    assert response.status_code == 204

    # Convert headers to dictionary for easier assertions
    headers_dict = headers_to_dict(response.headers)

    # Check that Access-Control-Allow-Origin is "*" and other headers are set correctly
    assert headers_dict["Access-Control-Allow-Origin"] == "*"
    assert headers_dict["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
    assert headers_dict["Access-Control-Allow-Headers"] == "Content-Type, Authorization"
    assert headers_dict["Access-Control-Allow-Credentials"] == "true"


# Test wildcard origin with a specific allowed origin that does not match
@pytest.mark.asyncio
async def test_cors_wildcard_with_specific_disallowed_origin(cors_middleware_all):
    # Override the allowed origins to only include "*"
    cors_middleware_all.allowed_origins = ["*"]

    # Create a request with an origin not explicitly in allowed origins
    scope = create_scope("GET", "/", headers={"Origin": "http://unlisted-origin.com"})
    request = Request(scope, receive=AsyncMock())
    event = Event(name="http.request.received", data={"request": request})

    # Process event through CORS middleware
    updated_event = await cors_middleware_all.before_request(event)
    response = Response(content="Hello, World", status_code=200)
    event.data['response'] = response

    # Process after_request to add CORS headers
    await cors_middleware_all.after_request(event)
    headers_dict = headers_to_dict(response.headers)

    # Ensure wildcard header "*" is set
    assert headers_dict["Access-Control-Allow-Origin"] == "*"
