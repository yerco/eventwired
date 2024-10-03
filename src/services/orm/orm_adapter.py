from abc import ABC, abstractmethod
from typing import Any, List, Type


class ORMAdapter(ABC):
    @abstractmethod
    async def create(self, model: Any, **data) -> Any:
        pass

    @abstractmethod
    async def get(self, model: Any, lookup_value: Any, column: str = None) -> Any:
        pass

    @abstractmethod
    async def update(self, model: Any, identifier: Any, identifier_column: Any, **data) -> Any:
        pass

    @abstractmethod
    async def delete(self, model: Any, identifier: Any) -> None:
        pass

    async def delete_by_column(self, model: Type[Any], column_name: str, value: Any) -> bool:
        pass

    @abstractmethod
    async def all(self, model: Any) -> List[Any]:
        pass

    @abstractmethod
    async def create_tables(self) -> None:
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        pass
