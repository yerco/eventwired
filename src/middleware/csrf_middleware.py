import secrets

from src.core.event_bus import EventBus, Event
from src.core.request import Request
from src.core.session import Session
from src.middleware.base_middleware import BaseMiddleware


class CSRFMiddleware(BaseMiddleware):
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def before_request(self, event):
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
                return await self.handle_csrf_failure(event)  # Custom handler for CSRF failure

        return event

    # Handle CSRF failure and send a meaningful response to the user
    async def handle_csrf_failure(self, event):
        await self.event_bus.publish(Event(name="http.error.403", data=event.data))

    async def after_request(self, event):
        return event
