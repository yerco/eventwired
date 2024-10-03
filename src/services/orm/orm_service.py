from typing import Any, Type
from sqlalchemy.ext.asyncio import create_async_engine
from src.services.config_service import ConfigService
from src.services.orm.sqlalchemy_adapter import SQLAlchemyAdapter


class ORMService:
    def __init__(self, config_service: ConfigService, Base=None):
        self.Base = Base  # SQLAlchemy Declarative Base
        self.config_service = config_service
        self.orm_adapter = None
        self.engine = None

    async def init(self, db_path: str = 'default.db'):
        db_url = self.config_service.get('DATABASE_URL', f'sqlite+aiosqlite:///{db_path}')
        # Initialize SQLAlchemy engine and adapter
        self.engine = create_async_engine(db_url, echo=False)
        self.orm_adapter = SQLAlchemyAdapter(engine=self.engine, Base=self.Base)

    async def create_tables(self):
        # Ensure that the adapter exists and create the tables
        if self.orm_adapter:
            await self.orm_adapter.create_tables()
        else:
            raise ValueError("ORM Adapter is not initialized")

    # CRUD operations
    async def create(self, model: Any, **data: Any) -> Any:
        return await self.orm_adapter.create(model, **data)

    # Get operation by primary key or any specified column
    async def get(self, model: Any, lookup_value: Any, lookup_column: str = None) -> Any:
        return await self.orm_adapter.get(model, lookup_value, lookup_column=lookup_column)

    # Update an instance by a specified column, defaulting to primary key
    async def update(self, model: Any, lookup_value: Any, lookup_column: str = "id", return_instance: bool = False, **data: Any) -> Any:
        return await self.orm_adapter.update(model, lookup_value, lookup_column, return_instance=return_instance, **data)

    # Delete operation, either by primary key or a specific column
    async def delete(self, model: Any, lookup_value: Any = None, lookup_column: str = None) -> None:
        if lookup_column is None:
            # If no lookup column is provided, use primary key
            return await self.orm_adapter.delete(model, lookup_value)
        else:
            # Delete by specific column
            return await self.orm_adapter.delete_by_column(model, lookup_column, lookup_value)

    async def all(self, model: Any) -> list[Any]:
        return await self.orm_adapter.all(model)

    async def cleanup(self):
        if self.engine:
            await self.engine.dispose()
