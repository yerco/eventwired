import os

from datetime import timedelta
from typing import Any, Dict


class ConfigService:
    def __init__(self, config: Dict[str, Any] = None):
        self._config: Dict[str, Any] = config or {}
        self._load_default_config()

    def _load_default_config(self):
        self._config.update({
            'SECRET_KEY': os.getenv('SECRET_KEY', 'default_secret'),
            'PRUNE_INTERVAL': timedelta(minutes=5),
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///demo_app.db'),
            'TEMPLATE_DIR': 'src/templates',
            'ORM_ENGINE': 'SQLAlchemy',
            'DB_SESSION': None,
        })

    def load_app_config(self, app_config: Dict[str, Any]):
        self._config.update(app_config)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def load_from_env(self, key: str, default: Any = None) -> None:
        self._config[key] = os.getenv(key, default)
