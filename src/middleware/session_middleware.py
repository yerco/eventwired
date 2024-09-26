import secrets

from src.event_bus import Event
from src.middleware.base_middleware import BaseMiddleware
from src.services.session_service import SessionService
from src.core.session import Session


class SessionMiddleware(BaseMiddleware):
    def __init__(self, session_service: SessionService):
        self.session_service = session_service

    async def before_request(self, event: Event) -> Event:
        # Extract the session ID from the cookie (or header) in the request
        request = event.data['request']
        session_id = request.cookies.get('session_id')  # Using cookies here, adjust for your framework

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
            if 'response_headers' not in event.data:
                event.data['response_headers'] = []

            session_id = session.session_id
            # print(f"Setting session cookie with ID: {session_id}")
            event.data['response_headers'].append((
                'Set-Cookie', f'session_id={session.session_id}; Path=/; HttpOnly; Secure; SameSite=Strict'))
            # print(f"Set-Cookie header added with session_id: {session.session_id}")

        return event
