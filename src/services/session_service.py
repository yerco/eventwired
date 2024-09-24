import datetime
import json

from src.services.orm.orm_service import ORMService
from src.models.session import Session as SessionModel

from demo_app.services.config_service import AppConfigService


class SessionService:
    def __init__(self, orm_service: ORMService, config_service: AppConfigService):
        self.orm_service = orm_service
        self.config_service = config_service

    async def load_session(self, session_id: str) -> dict:
        # If no session ID is provided, return an empty session
        if not session_id:
            return {}

        # Load session data from the database (or other storage)
        session = await self.orm_service.get_by_column(SessionModel, "session_id", session_id)
        if session:
            if session.expires_at and session.expires_at < datetime.datetime.utcnow():
                # Session has expired
                await self.orm_service.delete(SessionModel, session_id)
                return {}
            return json.loads(session.session_data)  # Deserialize session data from storage
        else:
            return {}

    async def save_session(self, session_id: str, session_data: dict) -> None:
        session_data_serialized = json.dumps(session_data)  # Serialize session data for storage

        session_duration = self.config_service.get("SESSION_EXPIRY_SECONDS", 3600)
        # Check if session already exists
        session = await self.orm_service.get_by_column(SessionModel, "session_id", session_id)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=session_duration)

        if session:
            # Update existing session
            await self.orm_service.update(SessionModel, session_id, session_data=session_data_serialized,
                                          expires_at=expires_at)
        else:
            # Create a new session
            await self.orm_service.create(SessionModel, session_id=session_id, session_data=session_data_serialized,
                                          expires_at=expires_at)

    async def delete_session(self, session_id: str) -> None:
        await self.orm_service.delete(SessionModel, session_id=session_id)

