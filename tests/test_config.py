import importlib
from datetime import timedelta

import pytest

from src.services.config_service import ConfigService
from src.config import DEFAULT_CONFIG


@pytest.fixture
def user_config():
    return {
        'ENVIRONMENT': 'production',
        'DATABASE_URL': 'postgresql://user:password@localhost:5432/mydb',
        'NEW_SETTING': 'new_value'
    }


# Test that ConfigService loads the default configuration from src/config.py
def test_load_default_config():
    config_service = ConfigService()

    for key, value in DEFAULT_CONFIG.items():
        assert config_service.get(key) == value, f"Default config for {key} does not match"


# Test that user_config overrides the default configuration
def test_load_user_config_overrides_defaults(user_config):
    config_service = ConfigService(user_config=user_config)

    # Check overridden values
    assert config_service.get('ENVIRONMENT') == 'production'
    assert config_service.get('DATABASE_URL') == 'postgresql://user:password@localhost:5432/mydb'

    # Check new settings are added
    assert config_service.get('NEW_SETTING') == 'new_value'

    # Check that other defaults are still intact
    assert config_service.get('SECRET_KEY') == DEFAULT_CONFIG['SECRET_KEY']
    assert config_service.get('PRUNE_INTERVAL') == DEFAULT_CONFIG['PRUNE_INTERVAL']


# Test that load_app_config method updates the configuration
def test_load_app_config():
    initial_config = {
        'ENVIRONMENT': 'staging',
        'DEBUG': True
    }
    config_service = ConfigService(initial_config)

    # New app config to load
    app_config = {
        'DEBUG': False,
        'NEW_FEATURE_ENABLED': True
    }

    config_service.load_app_config(app_config)

    # Check updated and new values
    assert config_service.get('ENVIRONMENT') == 'staging'  # Unchanged
    assert config_service.get('DEBUG') == False
    assert config_service.get('NEW_FEATURE_ENABLED') == True

    # Ensure defaults are still intact
    assert config_service.get('SECRET_KEY') == DEFAULT_CONFIG['SECRET_KEY']


# Test the set and get methods of ConfigService
def test_set_and_get_config():
    config_service = ConfigService()

    # Set a new value
    config_service.set('CACHE_TIMEOUT', 300)
    assert config_service.get('CACHE_TIMEOUT') == 300

    # Update an existing value
    config_service.set('ENVIRONMENT', 'testing')
    assert config_service.get('ENVIRONMENT') == 'testing'


# Test the load_from_env method, ensuring environment variables are loaded correctly
def test_load_from_env(monkeypatch):
    # Mock environment variable 'SECRET_KEY'
    monkeypatch.setenv('SECRET_KEY', 'env_secret_key')

    config_service = ConfigService()
    config_service.load_from_env('SECRET_KEY')

    assert config_service.get('SECRET_KEY') == 'env_secret_key'

    # Test with a key that doesn't exist in env
    config_service.load_from_env('NON_EXISTENT_KEY', default='default_value')
    assert config_service.get('NON_EXISTENT_KEY') == 'default_value'


# Ensure that default values are used when environment variables are not set
def test_default_values_when_env_not_set(monkeypatch):
    # Remove 'SECRET_KEY' and 'DATABASE_URL' from environment variables if they exist
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.delenv('DATABASE_URL', raising=False)

    config_service = ConfigService()

    assert config_service.get('SECRET_KEY') == 'default_secret'
    assert config_service.get('DATABASE_URL') == 'sqlite+aiosqlite:///eventwired.db'



# Ensure that PRUNE_INTERVAL is of type timedelta
def test_prune_interval_type():
    config_service = ConfigService()
    prune_interval = config_service.get('PRUNE_INTERVAL')
    assert isinstance(prune_interval, timedelta), "PRUNE_INTERVAL should be a timedelta instance"


# Check that the ENVIRONMENT default is 'development'
def test_environment_defaults():
    config_service = ConfigService()
    assert config_service.get('ENVIRONMENT') == 'development'


# Test the full configuration setup with default and user configurations
def test_full_configuration():
    user_config = {
        'ENVIRONMENT': 'production',
        'USE_REDIS_FOR_CQRS': True
    }
    config_service = ConfigService(user_config=user_config)

    # Check user overrides
    assert config_service.get('ENVIRONMENT') == 'production'
    assert config_service.get('USE_REDIS_FOR_CQRS') is True

    # Check defaults remain for other settings
    assert config_service.get('DELETE_EXPIRED_SESSIONS') == False
    assert config_service.get('CSRF_REDIRECT_ON_FAILURE') == False
