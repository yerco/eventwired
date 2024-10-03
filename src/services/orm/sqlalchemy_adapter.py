from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import select, delete as sqlalchemy_delete, update as sqlalchemy_update
from sqlalchemy import inspect
from typing import Any, Type, List

from src.services.orm.orm_adapter import ORMAdapter


class SQLAlchemyAdapter(ORMAdapter):
    def __init__(self, engine: AsyncEngine, Base):
        self.engine = engine
        self.Base = Base
        self.Session: sessionmaker = sessionmaker(
            bind=engine, class_=AsyncSession, expire_on_commit=False
        )

    async def create_tables(self):
        try:
            # Print the database URL being used
            # print(f"Creating tables in database: {self.engine.url}")
            async with self.engine.begin() as conn:
                await conn.run_sync(self.Base.metadata.create_all)
        except SQLAlchemyError as e:
            print(f"Error creating tables: {e}")
            raise

    async def create(self, model: Type[Any], **data: Any) -> Any:
        async with self.Session() as session:
            try:
                instance = model(**data)
                session.add(instance)
                await session.commit()
                return instance
            except IntegrityError as e:
                await session.rollback()
                print(f"IntegrityError during 'create': {e}")
                raise
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"SQLAlchemyError during 'create': {e}")
                raise

    async def get(self, model: Type[Any], lookup_value: Any, lookup_column: str = None) -> Any:
        async with self.Session() as session:
            try:
                # Default to the primary key if no column is provided
                if lookup_column is None:
                    lookup_column = inspect(model).primary_key[0].name

                stmt = select(model).where(getattr(model, lookup_column) == lookup_value)
                result = await session.execute(stmt)
                return result.scalars().one_or_none()
            except SQLAlchemyError as e:
                print(f"SQLAlchemyError during 'get': {e}")
                raise

    async def update(self, model: Type[Any], lookup_value: Any, lookup_column: str = "id", return_instance: bool = False, **data: Any) -> Any:
        if not data:
            return None

        async with self.Session() as session:
            try:
                # Update the record with the provided data and return the updated instance
                stmt = (
                    sqlalchemy_update(model)
                    .where(getattr(model, lookup_column) == lookup_value)
                    .values(**data)
                    .returning(*model.__table__.columns)  # Use RETURNING to get the updated row
                    .execution_options(synchronize_session="fetch")
                )
                result = await session.execute(stmt)
                await session.commit()

                # If return_instance is requested, extract the updated instance
                updated_instance_row = result.fetchone()
                if updated_instance_row:
                    updated_instance = model(**updated_instance_row._asdict())
                    return updated_instance if return_instance else True

                return False  # No rows were updated
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"SQLAlchemyError during 'update': {e}")
                raise

    # Delete by primary key value
    async def delete(self, model: Type[Any], lookup_value: Any) -> bool:
        async with self.Session() as session:
            try:
                # Dynamically retrieve the primary key column name for the given model
                primary_key_column = inspect(model).primary_key[0].name

                # Create the DELETE statement based on the primary key column
                stmt = (
                    sqlalchemy_delete(model)
                    .where(getattr(model, primary_key_column) == lookup_value)
                    .returning(getattr(model, primary_key_column))  # Return the primary key column value instead of assuming it's "id"
                )
                result = await session.execute(stmt)
                await session.commit()

                deleted_row = result.fetchone()
                return deleted_row is not None  # Return True if a row was deleted, otherwise False
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"SQLAlchemyError during 'delete': {e}")
                raise

    # Delete by any specific column value
    async def delete_by_column(self, model: Type[Any], column_name: str, value: Any) -> bool:
        async with self.Session() as session:
            try:
                # Get the actual primary key column name of the model
                primary_key_column = inspect(model).primary_key[0].name
                stmt = (
                    sqlalchemy_delete(model)
                    .where(getattr(model, column_name) == value)
                    .returning(getattr(model, primary_key_column))
                )
                result = await session.execute(stmt)
                await session.commit()

                deleted_row = result.fetchone()
                return deleted_row is not None  # Return True if a row was deleted, otherwise False
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"SQLAlchemyError during 'delete_by_column': {e}")
                raise

    async def all(self, model: Type[Any]) -> List[Any]:
        async with self.Session() as session:
            try:
                stmt = select(model)
                result = await session.execute(stmt)
                return result.scalars().all()
            except SQLAlchemyError as e:
                print(f"SQLAlchemyError during 'all': {e}")
                raise

    async def cleanup(self):
        await self.engine.dispose()
