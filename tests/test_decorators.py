import pytest
from unittest.mock import AsyncMock, MagicMock
from src.core.context_manager import set_container
from src.core.decorators import inject


# Mock services for testing
class MockService:
    def execute(self):
        return "Service Executed"


class AnotherService:
    def perform(self):
        return "Another Service Performed"


@pytest.fixture
def container():
    # Mock DI container
    mock_container = MagicMock()
    set_container(mock_container)
    yield mock_container
    set_container(None)


def test_resolve(container):
    # Test the resolve function
    container.get.return_value = MockService()
    from src.core.decorators import resolve

    service = resolve("MockService")
    assert service.execute() == "Service Executed"
    container.get.assert_called_once_with("MockService")


@pytest.mark.asyncio
async def test_inject_basic(container):
    # Test basic dependency injection
    container.get = AsyncMock(side_effect=lambda service_name: {"MockService": MockService()}.get(service_name))

    @inject
    async def example_function(mock_service: MockService):
        return mock_service.execute()

    result = await example_function()
    assert result == "Service Executed"
    container.get.assert_called_once_with("MockService")


@pytest.mark.asyncio
async def test_inject_with_override(container):
    # Test explicit parameter overriding
    container.get = AsyncMock(side_effect=lambda service_name: {"MockService": MockService()}.get(service_name))

    @inject
    async def example_function(mock_service: MockService):
        return mock_service.execute()

    # Override the injected parameter
    result = await example_function(mock_service=MockService())
    assert result == "Service Executed"
    # Ensure the container was not called because the argument was overridden
    container.get.assert_not_called()


@pytest.mark.asyncio
async def test_inject_missing_dependency(container):
    # Test missing dependency in the DI container
    container.get = AsyncMock(return_value=None)

    @inject
    async def example_function(mock_service: MockService):
        return mock_service.execute()

    with pytest.raises(AttributeError):
        await example_function()


@pytest.mark.asyncio
async def test_inject_mixed_arguments(container):
    # Test a function with mixed arguments
    container.get = AsyncMock(side_effect=lambda service_name: {"MockService": MockService()}.get(service_name))

    @inject
    async def example_function(mock_service: MockService, another_service: AnotherService = None):
        if another_service:
            return another_service.perform()
        return mock_service.execute()

    # Call with and without optional argument
    result_with_mock = await example_function()
    assert result_with_mock == "Service Executed"

    another_service = AnotherService()
    result_with_another = await example_function(another_service=another_service)
    assert result_with_another == "Another Service Performed"


def test_inject_non_async_function(container):
    # Test injection on a non-async function
    container.get_sync = MagicMock(side_effect=lambda service_name: {"MockService": MockService()}.get(service_name))

    @inject
    def example_function(mock_service: MockService):
        return mock_service.execute()

    result = example_function()
    assert result == "Service Executed"
    container.get_sync.assert_called_once_with("MockService")


@pytest.mark.asyncio
async def test_inject_no_annotations(container):
    # Test a function without annotations
    @inject
    async def example_function():
        return "No Dependencies"

    result = await example_function()
    assert result == "No Dependencies"
    container.get.assert_not_called()


@pytest.mark.asyncio
async def test_inject_partial_arguments(container):
    # Test partial arguments passed
    container.get = AsyncMock(side_effect=lambda service_name: {"MockService": MockService()}.get(service_name))

    @inject
    async def example_function(arg1, mock_service: MockService):
        return f"{arg1}, {mock_service.execute()}"

    result = await example_function("Hello")
    assert result == "Hello, Service Executed"
    container.get.assert_called_once_with("MockService")
