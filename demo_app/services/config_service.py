import os

from src.services.config_service import ConfigService as BaseConfigService


class AppConfigService(BaseConfigService):
    def __init__(self):
        super().__init__()
        self._load_app_specific_config()

    def _load_app_specific_config(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.set('BASE_DIR', base_dir)
        self.set('TEMPLATE_DIR', os.path.join(base_dir, '../templates'))
        self.set('TEMPLATE_ENGINE', 'JinjaAdapter')
        self.set('SESSION_EXPIRY_SECONDS', 3600)  # Default: 1 hour
        self.set('USE_REDIS_FOR_CQRS', True)
