from src.core.decorators import inject
from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController
from src.services.jwt_service import JWTService
from src.services.orm_service import ORMService
from src.services.password_service import PasswordService
from src.services.security.authentication_service import AuthenticationService

from demo_app.models.user import User


@inject
async def api_create_user_controller(event: Event, password_service: PasswordService, orm_service: ORMService):
    controller = HTTPController(event)

    request = event.data['request']
    http_method = request.method

    if http_method == "POST":
        json_data = await request.json()
        username = json_data.get('username')
        password = json_data.get('password')

        user_exists = await orm_service.filter(User, lookup_value=username, lookup_column="username")
        if user_exists:
            await controller.send_json({"error":"Username already exists."}, status=400)
        else:
            try:
                _password = password_service.hash_password(password)
                await orm_service.create(User, username=username, password=_password)
                await controller.send_json({"message": "User created successfully"}, status=201)
            except Exception as e:
                await controller.send_json({"error": f"User creation failed: {e}"}, status=400)


@inject
async def api_login_controller(event: Event, auth_service: AuthenticationService, jwt_service: JWTService):
    controller = HTTPController(event)
    request = event.data['request']

    if request.method == 'POST':
        json_data = await request.json()  # Assuming JSON payload
        username = json_data.get('username')
        password = json_data.get('password')

        # Use AuthenticationService to authenticate the user
        user = await auth_service.authenticate_user(User, username, password)

        if user:
            # Generate JWT token
            payload = {
                "user_id": user.id,
                "username": user.username
            }
            token = await jwt_service.generate_token(payload)
            await controller.send_json({"token": token}, status=200)
        else:
            await controller.send_json({"error": "Invalid credentials"}, status=401)


@inject
async def api_protected_controller(event: Event, jwt_service: JWTService):
    controller = HTTPController(event)
    request = event.data.get('request')
    auth_header = request.headers.get('authorization')

    # Check if Authorization header is present
    if not auth_header or not auth_header.startswith("Bearer "):
        await controller.send_json({"error": "Missing or invalid authorization header"}, status=401)
        return

    # Extract token
    token = auth_header.split(" ")[1]

    try:
        # Validate token using JWTService
        payload = await jwt_service.validate_token(token)

        # Token is valid, proceed to handle the protected resource
        # For example, returning some protected data
        protected_data = {"message": "This is protected content", "user_id": payload.get("user_id")}
        await controller.send_json(protected_data, status=200)

    except ValueError as e:
        # Token is invalid or expired
        await controller.send_json({"error": str(e)}, status=401)
