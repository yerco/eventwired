import os
import pytest
import re

from src.core.context_manager import set_container
from src.core.dicontainer import DIContainer
from src.test_utils.test_client import EWTestClient
from src.core.framework_app import FrameworkApp

from demo_app.routes import register_routes


@pytest.fixture
async def test_client():
    container = DIContainer()
    set_container(container)

    # Get three levels up from the current file’s directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_config = {
        'BASE_DIR': base_dir,
        'SECRET_KEY': 'supersecretkey',
        "STATIC_DIR": "demo_app/static",  # User-defined static directory
        "STATIC_URL_PATH": "/static",  # User-defined static URL path
        'USE_REDIS_FOR_CQRS': False,
        'SESSION_EXPIRY_SECONDS': 7200,  # Extend session expiry to 2 hours
        'TEMPLATE_ENGINE': 'JinjaAdapter',
        'TEMPLATE_DIR': os.path.join(base_dir, 'templates'),
        'DATABASE_URL': 'sqlite+aiosqlite:///test_db.db',
        'JWT_SECRET_KEY': 'my_secret_key',
        'JWT_ALGORITHM': 'HS256',
        'JWT_EXPIRATION_SECONDS': 7200,  # 2 hours expiration time
        'ENABLE_CSRF': True,
    }
    app = FrameworkApp(container, register_routes)
    await app.setup()

    return EWTestClient(app)


@pytest.fixture(autouse=True)
def test_db_cleanup():
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


# Extract CSRF token from HTML using regex
def extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([a-zA-Z0-9]+)"', html)
    if match:
        return match.group(1)
    raise ValueError("CSRF token not found in HTML.")


@pytest.mark.asyncio
async def test_invalid_registration_missing_csrf(test_client):
    response = await test_client.post(
        "/register",
        form_data={
            "username": "newuser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!"
        }
    )
    assert response.status_code == 403, "No CSRF token provided, so registration should fail."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_valid_registration(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."

    csrf_token = extract_csrf_token(response.body)

    response = await test_client.post(
        "/register",
        form_data={
            "username": "newuser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 201, "CSRF token provided, so registration should succeed."
    assert "Registration Successful!" in response.body, "Success message should be displayed."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_password_mismatch(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."

    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "newuser",
            "password": "StrongPass123!",
            "confirm_password": "MismatchPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 400, "Registration should fail if passwords do not match."
    assert "Passwords do not match" in response.body, "Error message should indicate password mismatch."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_username_already_exists(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."

    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "existinguser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 201, "Registration should succeed for valid input."
    assert "Registration Successful!" in response.body, "Success message should be displayed."

    # Go again to register with the same username
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."

    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "existinguser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 400, "Registration should fail if username is already taken."
    assert "Username already exists" in response.body, "Error message should indicate username conflict."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_missing_username(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)

    response = await test_client.post(
        "/register",
        form_data={
            "username": "",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 400, "Registration should fail if username is missing."
    assert "This field is required" in response.body, "Error message should indicate missing username."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_missing_password(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "newuser",
            "password": "",
            "confirm_password": "",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 400, "Registration should fail if password is missing."
    assert "This field is required" in response.body, "Error message should indicate missing password."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


# @pytest.mark.asyncio
# async def test_weak_password(test_client):
#     response = await test_client.post(
#         "/register",
#         form_data={
#             "username": "newuser",
#             "password": "weak",
#             "confirm_password": "weak"
#         }
#     )
#     assert response.status_code == 400, "Registration should fail if password is too weak."
#     assert "Password is too weak" in response.body, "Error message should indicate weak password."


@pytest.mark.asyncio
async def test_invalid_username_format(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "invalid username",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 400, "Registration should fail for invalid username format."
    assert "Username cannot contain whitespace" in response.body, "Error message should indicate username format issue."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_missing_csrf_token(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "newuser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            # No CSRF token provided
        },
        headers={}  # CSRF token intentionally missing
    )
    assert response.status_code == 403, "Registration should fail if CSRF token is missing."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_invalid_csrf_token(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "newuser",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": "invalid_token",
        },
    )
    assert response.status_code == 403, "Registration should fail if CSRF token is invalid."
    # assert "Invalid CSRF token" in response.body, "Error message should indicate invalid CSRF token."


@pytest.mark.asyncio
async def test_long_username(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)

    long_username = "a" * 256  # Exceeding typical length limits
    response = await test_client.post(
        "/register",
        form_data={
            "username": long_username,
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token,
        }
    )
    assert response.status_code == 400, "Registration should fail for excessively long username."
    assert "Username must be between 3 and 30 characters long" in response.body, "Error message should indicate long username."


@pytest.mark.asyncio
async def test_sql_injection_prevention(test_client):
    response = await test_client.get("/register")
    assert response.status_code == 200, "Expected status code 200."
    csrf_token = extract_csrf_token(response.body)
    response = await test_client.post(
        "/register",
        form_data={
            "username": "'; DROP TABLE users; --",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "csrf_token": csrf_token
        }
    )
    assert response.status_code == 400, "Registration should fail for SQL injection attempt."
    assert "Username cannot contain whitespace" in response.body, "Error message should indicate invalid username."
    assert "Username can only contain letters, numbers, and underscores" in response.body, "Error message should indicate invalid username."


# @pytest.mark.asyncio
# async def test_registration_rate_limiting(test_client):
#     response = await test_client.get("/register")
#     assert response.status_code == 200, "Expected status code 200."
#     csrf_token = extract_csrf_token(response.body)
#     for _ in range(5):
#         response = await test_client.post(
#             "/register",
#             form_data={
#                 "username": "user",
#                 "password": "StrongPass123!",
#                 "confirm_password": "StrongPass123!",
#                 "csrf_token": csrf_token
#             }
#         )
#     response = await test_client.post(
#         "/register",
#         form_data={
#             "username": "newuser",
#             "password": "StrongPass123!",
#             "confirm_password": "StrongPass123!"
#         }
#     )
#     assert response.status_code == 429, "Rate-limiting should trigger after multiple attempts."
#     assert "Too many registration attempts" in response.body, "Error message should indicate rate-limiting."
