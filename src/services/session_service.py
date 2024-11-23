import datetime
import json

from src.services.orm_service import ORMService
from src.models.session import Session as SessionModel
from src.services.config_service import ConfigService


class SessionService:
    def __init__(self, orm_service: ORMService, config_service: ConfigService):
        self.orm_service = orm_service
        self.config_service = config_service

    async def load_session(self, session_id: str) -> dict:
        # If no session ID is provided, return an empty session
        if not session_id:
            print(f"Session {session_id} not found.")
            return {}

        # Load session data from the database (or other storage)
        try:
            session = await self.orm_service.get(SessionModel, lookup_value=session_id, lookup_column="session_id")
        except Exception as e:
            print(f"Error fetching session {session_id}: {e}")
            return {}
        if session:
            # Check if the session has expired
            if session.expires_at:
                if session.expires_at.tzinfo is None:  # Check if it's naive
                    session.expires_at = session.expires_at.replace(tzinfo=datetime.timezone.utc)
                delete_expired_sessions = self.config_service.get("DELETE_EXPIRED_SESSIONS", False)
                if session.expires_at < datetime.datetime.now(datetime.timezone.utc):
                    if delete_expired_sessions:
                        # Session has expired; delete it and return an empty session
                        await self.orm_service.delete(SessionModel, session_id)
                    return {}

            # Attempt to deserialize session data
            try:
                return json.loads(session.session_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding session data for {session_id}: {e}")
            return {}
        else:
            return {}

    async def save_session(self, session_id: str, session_data: dict) -> None:
        session_data_serialized = json.dumps(session_data)  # Serialize session data for storage
        session_duration = self.config_service.get("SESSION_EXPIRY_SECONDS", 3600)
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=session_duration)

        # Check if session already exists
        session = await self.orm_service.get(SessionModel, lookup_value=session_id, lookup_column="session_id")

        current_time = datetime.datetime.now(datetime.timezone.utc)  # Get the current UTC time once for consistency
        if session:
            # Update existing session
            await self.orm_service.update(
                SessionModel,
                lookup_value=session_id,
                lookup_column="session_id",
                session_data=session_data_serialized,
                expires_at=expires_at,
                updated_at=current_time
            )
        else:
            # Create a new session
            await self.orm_service.create(
                SessionModel,
                session_id=session_id,
                session_data=session_data_serialized,
                created_at=current_time,
                updated_at=current_time,
                expires_at=expires_at
            )

    async def delete_session(self, session_id: str) -> None:
        await self.orm_service.delete(SessionModel, lookup_value=session_id, lookup_column='session_id')
