from src.core.event_bus import Event
from src.core.response import Response
from src.middleware.base_middleware import BaseMiddleware
from src.services.config_service import ConfigService
from src.services.session_service import SessionService
from src.core.session import Session


class BrowserSessionMiddleware(BaseMiddleware):
    def __init__(self, session_service: SessionService, config_service: ConfigService):
        self.session_service = session_service
        self.config_service = config_service

    async def before_request(self, event: Event) -> Event:
        # Extract the session ID from the cookie (or header) in the request
        request = event.data['request']
        session_id = request.cookies.get('session_id')  # Using cookies here

        if session_id:  # If a session ID exists in the cookies, load the session
            session_data = await self.session_service.load_session(session_id)
            if not session_data:  # Check if the session is empty (likely expired or nonexistent)
                await self.session_service.delete_session(session_id)  # Clean up the expired session
                session = Session(session_id=None)  # Generate a new session
                event.data['set_session_id'] = session.session_id  # Flag that a new session ID should be set
            else:
                session = Session(session_id, session_data)
        else:  # No session ID found, create a new session
            session = Session(session_id=None)  # Let it generate a new session ID
            event.data['set_session_id'] = session.session_id

        # Attach session data to the event so it can be accessed throughout the request lifecycle
        event.data['session'] = session

        return event

    async def after_request(self, event: Event) -> Event:
        # Access the session data from the event
        session: Session = event.data.get('session')
        session_id = session.session_id if session else None

        # Save the session if it was modified
        if session and session.is_modified():
            await self.session_service.save_session(session_id, session.data)

        # Optionally set a new session ID in the response headers (if the session was newly created)
        if 'set_session_id' in event.data:
            response: Response = event.data.get('response')
            if not response:
                # If no response object is available, create one for setting the cookie
                # TODO emit event?
                response = Response(content="", status_code=200)  # Adjust status/content as needed
                event.data['response'] = response


            # Determine environment-specific cookie settings
            is_production = self.config_service.get('ENVIRONMENT') == 'production'

            # Set the session cookie using the Response's set_cookie method
            response.set_cookie(
                name="session_id",
                value=session.session_id,
                path="/",
                http_only=is_production,  # Use HttpOnly in production
                secure=is_production,      # Use Secure flag for HTTPS in production
                same_site= "None" if is_production else "",  # Cross-origin in production
            )

        return event
