import pytest
import os
import sqlalchemy

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import declarative_base
from src.services.orm.sqlalchemy_adapter import SQLAlchemyAdapter


Base = declarative_base()


# Example model for SQLAlchemy
class ModelForTesting(Base):
    __tablename__ = 'test_model'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)


@pytest.fixture(scope="function")
def db_path():
    path = 'test_sqlalchemy.db'
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="function")
async def engine(db_path):
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def adapter(engine):
    adapter = SQLAlchemyAdapter(engine=engine, Base=Base)
    # Create tables before running each test
    await adapter.create_tables()
    yield adapter


@pytest.mark.asyncio
async def test_adapter_initialization(adapter, engine, db_path):
    assert adapter is not None, "SQLAlchemyAdapter should be initialized."
    assert isinstance(adapter.engine, AsyncEngine), "SQLAlchemyAdapter engine should be an AsyncEngine."
    assert adapter.engine is engine, "SQLAlchemyAdapter engine should be the same as the fixture engine."

    # Ensure the database file is created
    assert os.path.exists(db_path), "Database file should be created after table creation."


@pytest.mark.asyncio
async def test_create_tables(adapter, engine, db_path):
    # Clean up the file before starting the test to ensure it doesn't exist
    if os.path.exists(db_path):
        os.remove(db_path)

    # Ensure the database file does not exist before the test
    assert not os.path.exists(db_path), "Database file should not exist before table creation."

    # Call the method that creates the tables
    await adapter.create_tables()

    # Verify the database file is created after calling create_tables
    assert os.path.exists(db_path), "Database file should be created after calling create_tables."

    # Check if the table is created by reflecting the database schema
    async with engine.begin() as conn:
        result = await conn.run_sync(lambda conn: conn.dialect.has_table(conn, 'test_model'))

    assert result is True, "Table 'test_model' should exist in the database."


@pytest.mark.asyncio
async def test_create(adapter):
    # Test creating an instance of the model
    instance = await adapter.create(ModelForTesting, name="Test Instance")
    assert instance.id is not None, "The created instance should have an ID."
    assert instance.name == "Test Instance", "The name of the instance should be as expected."


@pytest.mark.asyncio
async def test_get(adapter):
    # Create a test instance
    created_instance = await adapter.create(ModelForTesting, name="Test Get")

    # Test getting the instance
    retrieved_instance = await adapter.get(ModelForTesting, created_instance.id)
    assert retrieved_instance is not None, "The instance should be retrieved."
    assert retrieved_instance.name == "Test Get", "The retrieved instance should have the correct name."


@pytest.mark.asyncio
async def test_update(adapter):
    # Create a test instance
    created_instance = await adapter.create(ModelForTesting, name="Original Name")

    # Test updating the instance
    updated_instance = await adapter.update(ModelForTesting, created_instance.id, name="Updated Name")
    assert updated_instance is not None, "The instance should be updated."
    assert updated_instance.name == "Updated Name", "The name of the instance should be updated."


@pytest.mark.asyncio
async def test_delete(adapter):
    # Create a test instance
    created_instance = await adapter.create(ModelForTesting, name="Test Delete")

    # Test deleting the instance
    delete_result = await adapter.delete(ModelForTesting, created_instance.id)
    assert delete_result is True, "The instance should be deleted."

    # Try to get the deleted instance
    deleted_instance = await adapter.get(ModelForTesting, created_instance.id)
    assert deleted_instance is None, "The instance should not exist after deletion."


@pytest.mark.asyncio
async def test_all(adapter):
    # Create multiple test instances
    await adapter.create(ModelForTesting, name="Instance 1")
    await adapter.create(ModelForTesting, name="Instance 2")

    # Test retrieving all instances
    all_instances = await adapter.all(ModelForTesting)
    assert len(all_instances) == 2, "There should be exactly two instances retrieved."
    assert all_instances[0].name == "Instance 1", "The first instance should have the correct name."
    assert all_instances[1].name == "Instance 2", "The second instance should have the correct name."
