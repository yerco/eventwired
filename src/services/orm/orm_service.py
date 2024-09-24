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

    async def get(self, model: Any, identifier: Any) -> Any:
        return await self.orm_adapter.get(model, identifier)

    async def get_by_column(self, model: Any, column: str, value: Any):
        return await self.orm_adapter.get_by_column(model, column, value)

    async def update(self, model: Any, identifier: Any, **data: Any) -> Any:
        return await self.orm_adapter.update(model, identifier, **data)

    async def delete(self, model: Any, identifier: Any = None, **column) -> None:
        if identifier:
            # Delete by identifier
            return await self.orm_adapter.delete(model, identifier)
        elif column:
            # Ensure only one column/value pair is provided
            if len(column) != 1:
                raise ValueError("Exactly one column must be provided for deletion by column.")

            # Extract the column name and value from the keyword arguments
            column_name, value = next(iter(column.items()))
            return await self.orm_adapter.delete_by_column(model, column_name, value)
        else:
            raise ValueError("Either identifier or a column-value pair must be provided for deletion.")

    async def all(self, model: Any) -> list[Any]:
        return await self.orm_adapter.all(model)

    async def cleanup(self):
        if self.engine:
            await self.engine.dispose()
