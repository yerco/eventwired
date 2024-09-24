from src.services.config_service import ConfigService


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
