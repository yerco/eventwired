from src.core.dicontainer import DIContainer
from src.core.event_bus import Event
from src.core.decorators import inject

from demo_app.models.event_log import EventLog


@inject
async def log_event_to_db(event: Event, container: DIContainer):
    orm_service = await container.get('ORMService')

    await orm_service.create(EventLog, event_name=event.name, additional_data=str(event.data))
