from src.event_bus import Event

from demo_app.di_setup import di_container
from demo_app.models.event_log import EventLog


async def log_event_to_db(event: Event):
    orm_service = await di_container.get('ORMService')

    await orm_service.create(EventLog, event_name=event.name, additional_data=str(event.data))
