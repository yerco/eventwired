from src.core.event_bus import Event
from src.core.decorators import inject
from src.services.orm_service import ORMService

from demo_app.models.event_log import EventLog


@inject
async def log_event_to_db(event: Event, orm_service: ORMService):
    await orm_service.create(EventLog, event_name=event.name, additional_data=str(event.data))
