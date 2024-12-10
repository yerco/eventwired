from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.middleware.base_middleware import BaseMiddleware
from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController


class JWTMiddleware(BaseMiddleware):
    def __init__(self, jwt_service, template_service=None):
        self.jwt_service = jwt_service
        self.template_service = template_service

    async def before_request(self, event: Event) -> Event:
        request = event.data.get('request')
        headers = dict(request.headers)
        auth_header = headers.get("authorization", "")
        controller = HTTPController(event, self.template_service)

        if not auth_header.startswith("Bearer "):
            await controller.send_json({"error": "Missing or invalid authorization header"}, status=401)
            return event

        token = self._get_token_from_header(auth_header)
        if not token:
            await controller.send_json({"error": "Invalid token format"}, status=401)
            return event

        try:
            payload = await self.jwt_service.validate_token(token)
            event.data["user"] = payload  # Attach user info to event data
        except ValueError as ve:
            await controller.send_json({"error": str(ve)}, status=401)
            event.data['response_already_sent'] = True

        return event  # Proceed with the request

    async def after_request(self, event: Event) -> None:
        # No action needed after request
        pass

    def _get_token_from_header(self, auth_header: str) -> str:
        parts = auth_header.split(" ")
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None
