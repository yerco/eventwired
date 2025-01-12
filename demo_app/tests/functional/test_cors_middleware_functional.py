import os
from unittest.mock import AsyncMock

import pytest

from demo_app.di_setup import setup_container
from src.core.context_manager import set_container
from src.core.dicontainer import DIContainer
from src.test_utils.test_client import EWTestClient
from src.core.framework_app import FrameworkApp

from demo_app.routes import register_routes


# Setup a test client
@pytest.fixture
async def test_client():
    test_config = {
        'CORS_ALLOWED_ORIGINS': ["http://allowed-origin.com", "http://*.example.com"],
        'CORS_ALLOWED_METHODS': ["GET", "POST", "OPTIONS"],
        'CORS_ALLOWED_HEADERS': ["Content-Type", "Authorization"],
        'CORS_ALLOW_CREDENTIALS': True,
        'DATABASE_URL': 'sqlite+aiosqlite:///test_db.db',
        'JWT_SECRET_KEY': 'test_secret_key',
    }
    container = DIContainer()
    await setup_container(container, test_config)
    set_container(container)

    app = FrameworkApp(container, register_routes)
    await app.setup()
    return EWTestClient(app)


# Convert a list of tuples to a dictionary
def get_headers_dict(headers_list):
    return {key.decode() if isinstance(key, bytes) else key: value.decode() if isinstance(value, bytes) else value
            for key, value in headers_list}


# I need to enable CORS
@pytest.mark.asyncio
async def test_cors_valid_origin(test_client):
    # Simulate a GET request from a valid origin
    response = await test_client.get(
        "/cors",
        headers={"Origin": "http://allowed-origin.com"}
    )
    assert response.status_code == 200

    headers = get_headers_dict(response.headers)

    assert headers["Access-Control-Allow-Origin"] == "http://allowed-origin.com"
    assert headers["Access-Control-Allow-Credentials"] == "true"
    if os.path.exists("test_db.db"):
        os.remove("test_db.db")


@pytest.mark.asyncio
async def test_cors_preflight_request(test_client):
    # Simulate a preflight (OPTIONS) request
    response = await test_client.options(
        "/cors",
        headers={
            "Origin": "http://allowed-origin.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
    )
    assert response.status_code == 204

    headers = get_headers_dict(response.headers)

    assert headers["Access-Control-Allow-Origin"] == "http://allowed-origin.com"
    assert headers["Access-Control-Allow-Methods"] == "GET, POST, OPTIONS"
    assert "Access-Control-Allow-Headers" in headers
    if os.path.exists("test_db.db"):
        os.remove("test_db.db")


@pytest.mark.asyncio
async def test_cors_invalid_origin(test_client):
    # Simulate a request from an invalid origin
    response = await test_client.get(
        "/cors",
        headers={"Origin": "http://unauthorized-origin.com"}
    )
    assert response.status_code == 200  # Request should proceed without CORS headers
    headers = get_headers_dict(response.headers)
    assert "Access-Control-Allow-Origin" not in headers
    if os.path.exists("test_db.db"):
        os.remove("test_db.db")


@pytest.mark.asyncio
async def test_cors_wildcard_origin(test_client):
    # Simulate a request from a wildcard-matching origin
    response = await test_client.get(
        "/cors",
        headers={"Origin": "http://sub.example.com"}
    )
    assert response.status_code == 200

    headers = get_headers_dict(response.headers)
    assert headers["Access-Control-Allow-Origin"] == "http://sub.example.com"
    assert headers["Access-Control-Allow-Credentials"] == "true"
    if os.path.exists("test_db.db"):
        os.remove("test_db.db")
