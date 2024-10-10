import os

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import declarative_base
from src.services.config_service import ConfigService
from src.services.orm_service import ORMService

Base = declarative_base()


# Test Models
class ModelForTestingOne(Base):
    __tablename__ = 'modelfortestingone'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)


class ModelForTestingTwo(Base):
    __tablename__ = 'modelfortestingtwo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    something = Column(String(50), nullable=False)


@pytest.fixture(scope="session")
async def orm_service():
    config_service = ConfigService()
    db_file = 'a_default.db'
    config_service.set('DATABASE_URL', f'sqlite+aiosqlite:///{db_file}')
    orm_service = ORMService(config_service, Base=Base)
    await orm_service.init()
    await orm_service.create_tables()  # Ensure tables are created before each test
    yield orm_service
    await orm_service.cleanup()

    # Ensure the database file is deleted after the tests
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(autouse=True)
async def reset_db(orm_service):
    # Reset the database before each test (clean slate)
    print("Resetting DB for the test")
    if orm_service.engine is not None:
        async with orm_service.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)  # Recreate tables
        Base.metadata.clear()


@pytest.mark.asyncio
async def test_orm_service_initialization(orm_service):
    assert orm_service is not None, "ORMService should be initialized."
    assert isinstance(orm_service.engine, AsyncEngine), "ORMService engine should be an AsyncEngine."
    assert os.path.exists('a_default.db'), "Database file should be created after table creation."


@pytest.mark.asyncio
async def test_create_sqlalchemy(orm_service):
    instance = await orm_service.create(ModelForTestingOne, name="Test Instance")
    assert instance.id is not None, "The created instance should have an ID."
    assert instance.name == "Test Instance", "The name of the instance should be as expected."


# Test to demonstrate get by primary key
@pytest.mark.asyncio
async def test_get_by_primary_key(orm_service):
    instance = await orm_service.create(ModelForTestingTwo, something="Test something")
    retrieved_instance = await orm_service.get(ModelForTestingTwo, instance.id)

    assert retrieved_instance.id == instance.id, "The retrieved instance ID should match the created instance ID."
    assert retrieved_instance.something == "Test something", "The retrieved instance data should match the created data."


@pytest.mark.asyncio
async def test_get_by_column(orm_service):
    # Arrange
    instance = await orm_service.create(ModelForTestingOne, name="Unique Name")

    # Act
    retrieved_instance = await orm_service.get(ModelForTestingOne, lookup_value="Unique Name", lookup_column="name")

    # Assert
    assert retrieved_instance.name == "Unique Name", "The retrieved instance should match the name 'Unique Name'."
    print(f"Successfully retrieved instance with name: {retrieved_instance.name}")


@pytest.mark.asyncio
async def test_get_nonexistent_instance(orm_service):
    # Act
    retrieved_instance = await orm_service.get(ModelForTestingOne, lookup_value=9999, lookup_column="id")  # ID that doesn't exist

    # Assert
    assert retrieved_instance is None, "The result should be None if the instance doesn't exist."
    print("Successfully handled retrieval of non-existent data.")


@pytest.mark.asyncio
async def test_update_by_primary_key(orm_service):
    # Create an instance for testing
    instance = await orm_service.create(ModelForTestingOne, name="Old Name")

    # Update the instance with a new name
    updated_instance = await orm_service.update(
        ModelForTestingOne,
        lookup_value=instance.id,
        name="Updated Name",
        return_instance=True  # Request the updated instance
    )

    # Assert that the instance name was updated correctly
    assert updated_instance.name == "Updated Name", "The instance name should be updated to 'Updated Name'."


@pytest.mark.asyncio
async def test_update_by_column(orm_service):
    instance = await orm_service.create(ModelForTestingOne, name="Old Name")

    updated_instance = await orm_service.update(
        ModelForTestingOne,
        lookup_value="Old Name",
        lookup_column="name",
        name="New Name",
        return_instance=True
    )

    assert updated_instance is not None, "The instance should have been found and updated."
    assert updated_instance.name == "New Name", "The instance name should be updated to 'New Name'."


@pytest.mark.asyncio
async def test_delete_sqlalchemy(orm_service):
    # Ensure the table is empty before the test
    all_instances = await orm_service.all(ModelForTestingOne)
    for instance in all_instances:
        await orm_service.delete(ModelForTestingOne, instance.id)

    instance = await orm_service.create(ModelForTestingOne, name="Test Instance")
    await orm_service.delete(ModelForTestingOne, instance.id)
    deleted_instance = await orm_service.get(ModelForTestingOne, instance.id)
    assert deleted_instance is None, "The instance should be deleted and no longer retrievable."


@pytest.mark.asyncio
async def test_delete_by_column_sqlalchemy(orm_service):
    # Step 1: Create instances
    await orm_service.create(ModelForTestingOne, name="Test Instance 1")
    await orm_service.create(ModelForTestingOne, name="Test Instance 2")

    # Step 2: Delete by column 'name'
    await orm_service.delete(ModelForTestingOne, lookup_column='name', lookup_value="Test Instance 1")

    # Step 3: Verify the instance was deleted
    remaining_instances = await orm_service.all(ModelForTestingOne)
    assert len(remaining_instances) == 1, "One instance should remain."
    assert remaining_instances[0].name == "Test Instance 2", "The correct instance should remain."


@pytest.mark.asyncio
async def test_all_sqlalchemy(orm_service):
    # Step 1: Ensure the table is empty before the test
    all_instances = await orm_service.all(ModelForTestingOne)
    for instance in all_instances:
        await orm_service.delete(ModelForTestingOne, instance.id)

    # Step 2: Create instances
    await orm_service.create(ModelForTestingOne, name="Test Instance 1")
    await orm_service.create(ModelForTestingOne, name="Test Instance 2")

    # Step 3: Fetch all instances and verify
    all_instances = await orm_service.all(ModelForTestingOne)
    assert len(all_instances) == 2, "Two instances should be fetched."
    assert all_instances[0].name == "Test Instance 1"
    assert all_instances[1].name == "Test Instance 2"


@pytest.mark.asyncio
async def test_cleanup_sqlalchemy(orm_service):
    assert orm_service.engine is not None, "The engine should be present."
    await orm_service.cleanup()
    try:
        async with orm_service.engine.connect() as conn:
            assert conn is not None, "Connection should still be possible after engine disposal."
    except Exception as e:
        pytest.fail(f"Engine raised an unexpected error after disposal: {e}")
