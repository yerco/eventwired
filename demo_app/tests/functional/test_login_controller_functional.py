import os
import pytest
import re

from src.core.setup_registry import run_setups
from src.services.orm_service import ORMService
from src.test_utils.test_client import EWTestClient
from src.core.framework_app import FrameworkApp
from src.models.session import Session

from demo_app.models.user import User
from demo_app.routes import register_routes
from demo_app.di_setup import di_container


# Provides a test client with FrameworkApp
@pytest.fixture
async def test_client():
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
        'ENVIRONMENT': 'production',
    }
    await run_setups(di_container, config=test_config)
    routing_service = await di_container.get('RoutingService')
    # Custom route registration logic for the user app
    await register_routes(routing_service)
    app = FrameworkApp()
    return EWTestClient(app)


@pytest.fixture(autouse=True)
def test_db_cleanup():
    yield
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.fixture
async def create_user():
    user_data = {
        "username": "testuser",
        "password": "password123"
    }
    orm_service: ORMService = await di_container.get('ORMService')
    await orm_service.create(User, username=user_data['username'], password=user_data['password'])


# Extract CSRF token from HTML using regex
def extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([a-zA-Z0-9]+)"', html)
    if match:
        return match.group(1)
    raise ValueError("CSRF token not found in HTML.")


@pytest.mark.asyncio
async def test_framework_GET_root_http_request_needs_CSRF(test_client, test_db_cleanup):
    response = await test_client.get("/")
    assert response.status_code == 200, "Expected status code 200."
    print("response headers:", response.headers)

    # Because at config.py 'ENABLE_CSRF': True, so the CSRF token should be generated
    # Find all 'set-cookie' headers in the response
    set_cookie_headers = [value for key, value in response.headers if key.lower() == 'set-cookie']

    # Define the CSRF token pattern
    csrf_token_pattern = re.compile(r'csrftoken=[a-f0-9]{64}')

    # Ensure at least one 'set-cookie' header contains the CSRF token
    assert any(csrf_token_pattern.search(cookie) for cookie in set_cookie_headers), \
        "CSRF token not found in 'set-cookie' headers."

    # Check for expected content in body
    assert "EVENTWIRED" in response.body, "'EVENTWIRED' not found in response body."


@pytest.mark.asyncio
async def test_login_valid_credentials(test_client, create_user, test_db_cleanup):
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
    csrf_response = await test_client.get("/login")
    csrf_token = extract_csrf_token(csrf_response.body)  # Implement extract_csrf_token as needed

    # Perform login
    response = await test_client.post(
        "/login",
        form_data={"username": "newuser", "password": "StrongPass123!", "csrf_token": csrf_token}
    )
    assert response.status_code == 200, "Login should succeed with valid credentials."
    assert "Welcome, newuser" in response.body, "User's successful login."
    assert "session_id" in response.cookies, "Session ID should be set on successful login."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_invalid_credentials(test_client, create_user):
    csrf_response = await test_client.get("/login")
    csrf_token = extract_csrf_token(csrf_response.body)

    # Attempt login with invalid password
    response = await test_client.post(
        "/login",
        form_data={"username": "validuser", "password": "wrongpassword", "csrf_token": csrf_token}
    )
    assert response.status_code == 401, "Login should fail with incorrect credentials. Unauthorized access."
    assert "session_id" not in response.cookies, "Session ID should not be set on failed login."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_missing_csrf_token(test_client, create_user):
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

    # Attempt login without CSRF token
    response = await test_client.post(
        "/login",
        form_data={"username": "newuser", "password": "StrongPass123!"}
    )
    assert response.status_code == 403, "Login should fail without CSRF token."
    assert "session_id" not in response.cookies, "Session ID should not be set without CSRF token."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_session_created(test_client, create_user):
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

    # Retrieve CSRF token
    csrf_response = await test_client.get("/login")
    csrf_token = extract_csrf_token(csrf_response.body)

    # Perform login
    response = await test_client.post(
        "/login",
        form_data={"username": "newuser", "password": "StrongPass123!", "csrf_token": csrf_token}
    )
    assert response.status_code == 200, "Login should succeed."
    session_id = response.cookies.get("session_id")
    assert session_id, "Session ID should be set in cookies."

    # Verify session exists in backend
    orm_service: ORMService = await di_container.get('ORMService')
    session = await orm_service.get(Session, session_id, 'session_id')
    assert session, "Session should exist in the backend."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')

@pytest.mark.asyncio
async def test_login_missing_fields(test_client):
    # Retrieve CSRF token
    csrf_response = await test_client.get("/login")
    csrf_token = extract_csrf_token(csrf_response.body)

    # Attempt login with missing username
    response = await test_client.post(
        "/login",
        form_data={"password": "validpassword", "csrf_token": csrf_token}
    )
    assert response.status_code == 400, "Login should fail with missing username."

    # Attempt login with missing password
    response = await test_client.post(
        "/login",
        form_data={"username": "validuser", "csrf_token": csrf_token}
    )
    assert response.status_code == 400, "Login should fail with missing password."
    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


@pytest.mark.asyncio
async def test_login_secure_http_only_cookies(test_client, create_user):
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

    # Perform login
    response = await test_client.post(
        "/login",
        form_data={"username": "newuser", "password": "StrongPass123!", "csrf_token": csrf_token}
    )
    assert response.status_code == 200

    # Check cookie attributes, ENVIROMENT is set to 'production'
    set_cookie_headers = [value for name, value in response.headers if name.lower() == 'set-cookie']
    assert set_cookie_headers, "No 'Set-Cookie' header found in response."
    http_only_found = any('HttpOnly' in header_value for header_value in set_cookie_headers)
    assert http_only_found, "Session cookie should be HttpOnly."
    secure_found = any('Secure' in header_value for header_value in set_cookie_headers)
    assert secure_found, "Session cookie should be Secure in production."

    if os.path.exists('test_db.db'):
        os.remove('test_db.db')


# @pytest.mark.asyncio
# async def test_brute_force_protection(test_client, create_user):
#     await create_user(username="validuser", password="validpassword")
#
#     # Retrieve CSRF token
#     csrf_response = await test_client.get("/login")
#     csrf_token = extract_csrf_token(csrf_response.body)
#
#     # Perform multiple invalid login attempts
#     for _ in range(5):
#         response = await test_client.post(
#             "/login",
#             form_data={"username": "validuser", "password": "wrongpassword", "csrf_token": csrf_token}
#         )
#         assert response.status_code == 401, "Login should fail with incorrect credentials."
#
#     # Assert rate-limiting or lockout mechanism is triggered
#     response = await test_client.post(
#         "/login",
#         form_data={"username": "validuser", "password": "wrongpassword", "csrf_token": csrf_token}
#     )
#     assert response.status_code == 429, "Too many attempts should trigger rate-limiting."


@pytest.mark.asyncio
async def test_session_expiry(test_client, create_user):
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

    # Retrieve CSRF token
    csrf_response = await test_client.get("/login")
    csrf_token = extract_csrf_token(csrf_response.body)

    # Perform login
    response = await test_client.post(
        "/login",
        form_data={"username": "newuser", "password": "StrongPass123!", "csrf_token": csrf_token}
    )
    session_id = response.cookies.get("session_id")
    assert session_id, "Session ID should be set."

    # Simulate session expiry
    orm_service: ORMService = await di_container.get('ORMService')
    result = await orm_service.delete(Session, session_id, 'session_id')
    print("Result:", result)

    # Attempt to use expired session
    response = await test_client.get("/hello", cookies={"session_id": session_id})
    assert response.status_code == 401, "Expired session should result in unauthorized access."
