from src.services.config_service import ConfigService


def test_config_values(monkeypatch):
    # Mock the ConfigService.get method to return a specific value based on the key
    monkeypatch.setattr(ConfigService, 'get', lambda self, key: f"mock_{key}")

    # Import the config values after mocking
    from src.config import secret_key, prune_interval, database_url

    # Assertions to check if the mocked values are set correctly
    assert secret_key == "mock_SECRET_KEY"
    assert prune_interval == "mock_PRUNE_INTERVAL"
    assert database_url == "mock_DATABASE_URL"
