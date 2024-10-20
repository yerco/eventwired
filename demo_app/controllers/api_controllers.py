from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.di_setup import di_container
from demo_app.models.user import User


async def api_login_controller(event: Event):
    auth_service = await di_container.get('AuthenticationService')
    jwt_service = await di_container.get('JWTService')

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


async def api_protected_controller(event: Event):
    jwt_service = await di_container.get('JWTService')
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
