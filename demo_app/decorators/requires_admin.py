from src.core.event_bus import Event
from src.core.decorators import inject
from src.controllers.http_controller import HTTPController
from src.services.session_service import SessionService
from src.services.security.authentication_service import AuthenticationService


def requires_admin(func):
    @inject
    async def wrapper(event: Event, session_service: SessionService, auth_service: AuthenticationService, *args, **kwargs):
        controller = HTTPController(event)
        session_id = controller.get_session_id()
        session = await session_service.load_session(session_id)

        if not session or not session.get("is_admin"):
            return await auth_service.send_unauthorized(event)

        return await func(event, *args, **kwargs)

    return wrapper
