from datetime import timedelta

import pytest

from src.services.config_service import ConfigService


@pytest.fixture
def default_config():
    return ConfigService()


@pytest.fixture
def user_config():
    return ConfigService({'TEST_KEY': 'test_value', 'DATABASE_URL': 'sqlite+aiosqlite:///test.db'})


def test_config_service():
    config_service = ConfigService({'TEST_KEY': 'test_value'})

    # Test getting a configuration value
    assert config_service.get('TEST_KEY') == 'test_value'

    # Test setting a configuration value
    config_service.set('NEW_KEY', 'new_value')
    assert config_service.get('NEW_KEY') == 'new_value'

    # Test loading from environment variables (you would mock os.getenv in a real test)
    config_service.load_from_env('API_KEY', 'MY_API_KEY')
    assert config_service.get('API_KEY') == 'MY_API_KEY'  # Assuming MY_API_KEY is not set in env


def test_load_default_config(default_config):
    # Test if default configuration values are loaded
    assert default_config.get('SECRET_KEY') == 'default_secret'
    assert default_config.get('PRUNE_INTERVAL') == timedelta(minutes=5)
    assert default_config.get('DATABASE_URL') == 'sqlite+aiosqlite:///eventwired.db'
    assert default_config.get('TEMPLATE_DIR') == 'src/templates'
    assert default_config.get('SESSION_EXPIRY_SECONDS') == 3600
    assert default_config.get('USE_REDIS_FOR_CQRS') is False


def test_load_user_config(user_config):
    # Test if user-provided configuration values override defaults
    assert user_config.get('TEST_KEY') == 'test_value'
    assert user_config.get('DATABASE_URL') == 'sqlite+aiosqlite:///test.db'


def test_get_non_existing_key(default_config):
    # Test that a non-existing key returns the default value
    assert default_config.get('NON_EXISTING_KEY', 'default_value') == 'default_value'


def test_set_value(default_config):
    # Test setting a configuration value
    default_config.set('NEW_KEY', 'new_value')
    assert default_config.get('NEW_KEY') == 'new_value'


def test_load_from_env(monkeypatch, default_config):
    # Mock the environment variable
    monkeypatch.setenv('API_KEY', 'mock_api_key')

    # Load from environment and assert it gets the value
    default_config.load_from_env('API_KEY')
    assert default_config.get('API_KEY') == 'mock_api_key'


def test_load_from_env_with_default(monkeypatch, default_config):
    # If the environment variable is not set, it should return the default value
    monkeypatch.delenv('UNSET_API_KEY', raising=False)
    default_config.load_from_env('UNSET_API_KEY', 'default_api_key')
    assert default_config.get('UNSET_API_KEY') == 'default_api_key'


def test_override_with_user_config(default_config):
    # Override with user-provided config and check
    app_config = {'USE_REDIS_FOR_CQRS': True, 'NEW_FEATURE_FLAG': True}
    default_config.load_app_config(app_config)

    assert default_config.get('USE_REDIS_FOR_CQRS') is True
    assert default_config.get('NEW_FEATURE_FLAG') is True


def test_no_override_when_value_not_provided(default_config):
    # If a value is not provided by the user, the default should be kept
    default_config.load_app_config({'NEW_KEY': 'new_value'})

    # Test a key that was not provided
    assert default_config.get('SECRET_KEY') == 'default_secret'

    # Test a key that was provided
    assert default_config.get('NEW_KEY') == 'new_value'
