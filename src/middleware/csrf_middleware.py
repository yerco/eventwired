import secrets

from src.core.event_bus import EventBus, Event
from src.core.request import Request
from src.core.response import Response
from src.core.session import Session
from src.middleware.base_middleware import BaseMiddleware
from src.services.config_service import ConfigService


class CSRFMiddleware(BaseMiddleware):
    def __init__(self, event_bus: EventBus, config_service: ConfigService):
        self.event_bus = event_bus
        self.config_service = config_service

    async def before_request(self, event) -> Event:
        request: Request = event.data['request']
        session: Session = event.data.get('session')

        # Ensure session is properly loaded
        if not session:
            raise Exception("Session not found in event")

        # Only generate a new CSRF token if none exists in the session (GET requests)
        csrf_token = session.data.get('csrf_token')
        if request.method == 'GET':
            if not csrf_token:
                csrf_token = secrets.token_hex(32)  # Generate new CSRF token
                session.set('csrf_token', csrf_token)  # Store CSRF token in session
            request.csrf_token = csrf_token  # Make token available for later, this is an "internal" request

        # CSRF protection for unsafe HTTP methods (POST, PUT, DELETE)
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token_from_session = session.data.get('csrf_token')
            csrf_token_from_request = (await request.form()).get('csrf_token')

            if isinstance(csrf_token_from_request, list):
                csrf_token_from_request = csrf_token_from_request[0]  # If it's a list, take the first item

            csrf_token_from_header = request.headers.get('X-CSRF-Token')

            # Validate CSRF token
            if not csrf_token_from_session or \
                    (csrf_token_from_session != csrf_token_from_request and
                     csrf_token_from_session != csrf_token_from_header):
                await self.handle_csrf_failure(event)  # Custom handler for CSRF failure

        return event

    # Handle CSRF failure and send a meaningful response to the user
    async def handle_csrf_failure(self, event):
        print("CSRF token mismatch detected.")
        if self.config_service.get("CSRF_REDIRECT_ON_FAILURE", False):
            await self.event_bus.publish(Event(name="http.error.no_csrf", data=event.data))
        else:
            await self.event_bus.publish(Event(name="http.error.403", data=event.data))

    async def after_request(self, event) -> Event:
        response: Response = event.data.get('response')
        request: Request = event.data['request']
        csrf_token = request.csrf_token

        if csrf_token and self.config_service.get('ENABLE_CSRF'):
            is_production = self.config_service.get('ENVIRONMENT') == 'production'
            response.set_cookie(
                name="csrftoken",
                value=csrf_token,
                path="/",
                http_only=is_production,  # Use HttpOnly for production to enhance security
                secure=is_production,  # Secure only for HTTPS in production
                same_site="None" if is_production else "",  # None for production, lax or empty for dev
            )

        return event
