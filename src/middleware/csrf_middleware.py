import secrets
from src.middleware.base_middleware import BaseMiddleware
from src.core.response import Response


class CSRFMiddleware(BaseMiddleware):
    async def before_request(self, event):
        request = event.data['request']
        session = event.data.get('session')

        # Ensure session is properly loaded
        if not session:
            raise Exception("Session not found in event")

        # Only generate a new CSRF token if none exists in the session (GET requests)
        csrf_token = session.data.get('csrf_token')
        if request.method == 'GET':
            if not csrf_token:
                csrf_token = secrets.token_hex(32)  # Generate new CSRF token
                session.set('csrf_token', csrf_token)  # Store CSRF token in session
            event.data['request'].set_cookie('csrf_token', csrf_token)  # Set CSRF token as a cookie

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
        response = Response(
            content="CSRF token invalid or missing. Please refresh the page and try again.",
            status_code=403,
            content_type='text/plain'
        )

        # Send the response to the client
        event.data['response'] = response
        return event

    async def after_request(self, event):
        return event
