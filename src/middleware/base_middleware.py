from abc import ABC, abstractmethod

from src.core.event_bus import Event


class BaseMiddleware(ABC):
    @abstractmethod
    async def before_request(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def after_request(self, event: Event) -> None:
        pass
