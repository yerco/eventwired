import pytest
import jwt
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

from src.services.jwt_service import JWTService


# Fixture for config_service mock
@pytest.fixture
def config_service_mock():
    return {
        'JWT_SECRET_KEY': 'test_secret',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION_SECONDS': 3600  # 1 hour
    }

# Fixture for JWTService instance
@pytest.fixture
def jwt_service(config_service_mock):
    return JWTService(config_service=config_service_mock)


# Test case: Generating a token
@pytest.mark.asyncio
async def test_generate_token(jwt_service):
    payload = {"user_id": 123, "username": "test_user"}
    token = await jwt_service.generate_token(payload)

    # Ensure token is a non-empty string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode the token to validate its contents
    decoded_payload = jwt.decode(token, jwt_service.secret_key, algorithms=[jwt_service.algorithm])
    assert decoded_payload["user_id"] == 123
    assert decoded_payload["username"] == "test_user"
    assert "iat" in decoded_payload
    assert "exp" in decoded_payload

    # Ensure the expiration time is correctly set (1 hour from now)
    current_time = datetime.now(timezone.utc)
    exp_time = datetime.fromtimestamp(decoded_payload["exp"], timezone.utc)
    assert timedelta(seconds=3600) - timedelta(seconds=5) <= exp_time - current_time <= timedelta(seconds=3600)


# Test case: Validating a valid token
@pytest.mark.asyncio
async def test_validate_token(jwt_service):
    payload = {"user_id": 123, "username": "test_user"}
    token = await jwt_service.generate_token(payload)

    # Ensure the token is validated and decoded correctly
    decoded_payload = await jwt_service.validate_token(token)
    assert decoded_payload["user_id"] == 123
    assert decoded_payload["username"] == "test_user"
    assert "iat" in decoded_payload
    assert "exp" in decoded_payload


# Test case: Validating an expired token
@pytest.mark.asyncio
async def test_validate_expired_token(jwt_service, monkeypatch):
    payload = {"user_id": 123, "username": "test_user"}

    # Freeze time to 2 hours in the past
    past_time = datetime.now(timezone.utc) - timedelta(hours=2)
    with freeze_time(past_time):
        token = await jwt_service.generate_token(payload)

    # Now that the time is reset, validate the token (which should be expired)
    with pytest.raises(ValueError, match="Token has expired"):
        await jwt_service.validate_token(token)


# Test case: Validating an invalid token (manipulated or forged)
@pytest.mark.asyncio
async def test_validate_invalid_token(jwt_service):
    invalid_token = "this.is.an.invalid.token"

    # Ensure validation raises an error for invalid tokens
    with pytest.raises(ValueError, match="Invalid token"):
        await jwt_service.validate_token(invalid_token)


# Test case: Token with custom expiration
@pytest.mark.asyncio
async def test_generate_token_custom_expiration(jwt_service, monkeypatch):
    # Override expiration_seconds for this test
    jwt_service.expiration_seconds = 7200  # 2 hours

    payload = {"user_id": 123, "username": "test_user"}
    token = await jwt_service.generate_token(payload)

    # Decode the token to check the expiration time
    decoded_payload = jwt.decode(token, jwt_service.secret_key, algorithms=[jwt_service.algorithm])
    exp_time = datetime.fromtimestamp(decoded_payload["exp"], timezone.utc)

    # Ensure the expiration time is 2 hours from now
    current_time = datetime.now(timezone.utc)
    assert timedelta(seconds=7200) - timedelta(seconds=5) <= exp_time - current_time <= timedelta(seconds=7200)


# Test case: Missing secret key in config
def test_missing_secret_key_in_config(monkeypatch):
    config_service_mock = {}
    # Expect a KeyError to be raised when JWT_SECRET_KEY is missing
    with pytest.raises(KeyError, match="JWT_SECRET_KEY is missing in the config"):
        JWTService(config_service=config_service_mock)


# Test case: Using an invalid secret key for token validation
@pytest.mark.asyncio
async def test_invalid_secret_key_for_validation(jwt_service):
    payload = {"user_id": 123, "username": "test_user"}
    token = await jwt_service.generate_token(payload)

    # Modify the secret key to simulate a validation failure
    jwt_service.secret_key = "wrong_secret_key"

    with pytest.raises(ValueError, match="Invalid token"):
        await jwt_service.validate_token(token)
