import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.middleware.jwt_middleware import JWTMiddleware
from src.event_bus import Event


@pytest.fixture
def jwt_service_mock():
    # Mock the JWT service
    service = AsyncMock()
    service.validate_token = AsyncMock(return_value={"user_id": 123})  # Return a valid payload asynchronously
    return service


@pytest.fixture
def event_mock():
    # Mock the event and request objects
    request_mock = MagicMock()
    request_mock.headers = {"authorization": "Bearer valid_token"}  # Use string for header to match str type expected

    event_data = {
        "request": request_mock,
        "send": AsyncMock(),
    }
    return Event(name="http.request.received", data=event_data)


@pytest.mark.asyncio
async def test_jwt_middleware_before_request_valid_token(monkeypatch, jwt_service_mock, event_mock):
    # Mock HTTPController
    controller_mock = AsyncMock()
    monkeypatch.setattr('src.controllers.http_controller.HTTPController', lambda event, _: controller_mock)

    middleware = JWTMiddleware(jwt_service_mock)

    # Call before_request
    await middleware.before_request(event_mock)

    # Assert token was validated and user info added to event
    jwt_service_mock.validate_token.assert_called_once_with("valid_token")

    # Ensure 'user' data is correctly set in the event
    assert event_mock.data['user'] == {"user_id": 123}


@pytest.mark.asyncio
async def test_jwt_middleware_before_request_invalid_token(monkeypatch, jwt_service_mock, event_mock):
    controller_mock = AsyncMock()

    def mock_controller(event, template_service=None):
        return controller_mock
    monkeypatch.setattr('src.middleware.jwt_middleware.HTTPController', mock_controller)

    jwt_service_mock.validate_token = AsyncMock(side_effect=InvalidTokenError)

    event_mock.data['request'].headers = {"authorization": "Bearer invalid_token"}

    middleware = JWTMiddleware(jwt_service_mock)
    await middleware.before_request(event_mock)

    jwt_service_mock.validate_token.assert_awaited_once_with("invalid_token")

    controller_mock.send_json.assert_awaited_once_with({"error": "Invalid or expired token"}, status=401)


@pytest.mark.asyncio
async def test_jwt_middleware_before_request_no_auth_header(monkeypatch, jwt_service_mock, event_mock):
    controller_mock = AsyncMock()

    def mock_controller(event, template_service=None):
        return controller_mock

    monkeypatch.setattr('src.middleware.jwt_middleware.HTTPController', mock_controller)

    event_mock.data['request'].headers = {}  # Empty headers (no Authorization header)

    middleware = JWTMiddleware(jwt_service_mock)
    await middleware.before_request(event_mock)

    # Corrected: pass the status first and then the message, as expected by send_error
    controller_mock.send_json.assert_awaited_once_with({'error': 'Missing or invalid authorization header'}, status=401)

    jwt_service_mock.validate_token.assert_not_called()


@pytest.mark.asyncio
async def test_jwt_middleware_before_request_expired_token(monkeypatch, jwt_service_mock, event_mock):
    # Mock HTTPController
    controller_mock = AsyncMock()

    def mock_controller(event, template_service=None):
        return controller_mock

    monkeypatch.setattr('src.middleware.jwt_middleware.HTTPController', mock_controller)

    # Set up the JWT service mock to raise an ExpiredSignatureError when validating the token
    jwt_service_mock.validate_token = AsyncMock(side_effect=ExpiredSignatureError)

    # Provide the expired token in the Authorization header
    event_mock.data['request'].headers = {"authorization": "Bearer expired_token"}

    # Create the middleware instance and call before_request
    middleware = JWTMiddleware(jwt_service_mock)
    await middleware.before_request(event_mock)

    # Ensure the JWT service tried to validate the expired token
    jwt_service_mock.validate_token.assert_awaited_once_with("expired_token")

    # Ensure the controller sent the correct error response
    controller_mock.send_json.assert_awaited_once_with({"error": "Invalid or expired token"}, status=401)


@pytest.mark.asyncio
async def test_jwt_middleware_before_request_no_token_after_bearer(monkeypatch, jwt_service_mock, event_mock):
    # Mock HTTPController
    controller_mock = AsyncMock()

    def mock_controller(event, template_service=None):
        return controller_mock

    monkeypatch.setattr('src.middleware.jwt_middleware.HTTPController', mock_controller)

    # Case 1: No token after "Bearer "
    event_mock.data['request'].headers = {"authorization": "Bearer "}  # No token after Bearer

    middleware = JWTMiddleware(jwt_service_mock)
    await middleware.before_request(event_mock)

    # Ensure the controller sent the correct error response for invalid token format
    controller_mock.send_json.assert_awaited_once_with({"error": "Invalid token format"}, status=401)
    jwt_service_mock.validate_token.assert_not_called()


@pytest.mark.asyncio
async def test_jwt_middleware_before_request_malformed_token(monkeypatch, jwt_service_mock, event_mock):
    # Mock HTTPController
    controller_mock = AsyncMock()

    def mock_controller(event, template_service=None):
        return controller_mock

    monkeypatch.setattr('src.middleware.jwt_middleware.HTTPController', mock_controller)

    # Case 2: Token that is just some malformed string
    event_mock.data['request'].headers = {"authorization": "Bearer someInvalidTokenString"}

    # Set up JWT service to raise InvalidTokenError (since the token format is wrong)
    jwt_service_mock.validate_token = AsyncMock(side_effect=InvalidTokenError)

    # Create the middleware instance and call before_request
    middleware = JWTMiddleware(jwt_service_mock)
    await middleware.before_request(event_mock)

    # Ensure the JWT service tried to validate the malformed token
    jwt_service_mock.validate_token.assert_awaited_once_with("someInvalidTokenString")

    # Ensure the controller sent the correct error response
    controller_mock.send_json.assert_awaited_once_with({"error": "Invalid or expired token"}, status=401)
