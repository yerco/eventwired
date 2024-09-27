from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.sql import select
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
            print(f"Creating tables in database: {self.engine.url}")
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

    async def get(self, model: Type[Any], identifier: Any) -> Any:
        async with self.Session() as session:
            try:
                # Dynamically get the primary key column
                primary_key_column = inspect(model).primary_key[0].name
                # Query based on the primary key column
                stmt = select(model).where(getattr(model, primary_key_column) == identifier)
                result = await session.execute(stmt)
                return result.scalars().one_or_none()
            except SQLAlchemyError as e:
                print(f"SQLAlchemyError during 'get': {e}")
                raise

    async def get_by_column(self, model: Type[Any], column: str, value: Any) -> Any:
        async with self.Session() as session:
            try:
                stmt = select(model).where(getattr(model, column) == value)
                result = await session.execute(stmt)
                return result.scalars().one_or_none()
            except SQLAlchemyError as e:
                print(f"SQLAlchemyError during 'get_by_column': {e}")
                raise

    async def update(self, model: Type[Any], identifier: Any, **data: Any) -> Any:
        if not data:
            return None
        async with self.Session() as session:
            try:
                instance = await self.get(model, identifier)
                if instance:
                    for key, value in data.items():
                        setattr(instance, key, value)
                    await session.commit()
                return instance
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"SQLAlchemyError during 'update': {e}")
                raise

    async def delete(self, model: Type[Any], identifier: Any) -> bool:
        async with self.Session() as session:
            try:
                instance = await self.get(model, identifier)
                if instance:
                    await session.delete(instance)
                    await session.commit()
                    return True
                return False
            except SQLAlchemyError as e:
                await session.rollback()
                print(f"SQLAlchemyError during 'delete': {e}")
                raise

    async def delete_by_column(self, model: Type[Any], column_name: str, value: Any) -> bool:
        async with self.Session() as session:
            try:
                # Query for the rows matching the condition (column_name == value)
                query = await session.execute(
                    select(model).filter(getattr(model, column_name) == value)
                )
                instances = query.scalars().all()

                # If instances are found, delete them
                if instances:
                    for instance in instances:
                        await session.delete(instance)
                    await session.commit()
                    return True
                return False
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
