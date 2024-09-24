from src.event_bus import Event


class PublisherService:
    def __init__(self, event_bus):
        self.event_bus = event_bus

    async def publish_logout_success(self, user_id: int):
        event = Event(name='user.logout.success', data={'user_id': user_id})
        await self.event_bus.publish(event)

    async def publish_logout_failure(self):
        event = Event(name='user.logout.failure', data={})
        await self.event_bus.publish(event)
