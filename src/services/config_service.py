import os

from typing import Any, Dict

from src.config import DEFAULT_CONFIG


class ConfigService:
    def __init__(self, user_config: Dict[str, Any] = None):
        self._config: Dict[str, Any] = {}
        self._load_default_config()
        if user_config:
            self._load_user_config(user_config)

    def _load_default_config(self):
        self._config.update(DEFAULT_CONFIG)

    def _load_user_config(self, user_config: Dict[str, Any]):
        self._config.update(user_config)

    def load_app_config(self, app_config: Dict[str, Any]):
        self._config.update(app_config)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def load_from_env(self, key: str, default: Any = None) -> None:
        self._config[key] = os.getenv(key, default)
