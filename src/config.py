import os
from datetime import timedelta

DEFAULT_CONFIG = {
    'SECRET_KEY': os.getenv('SECRET_KEY', 'default_secret'),
    'PRUNE_INTERVAL': timedelta(minutes=5),
    'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///eventwired.db'),
    'TEMPLATE_DIR': 'src/templates',
    'ORM_ENGINE': 'SQLAlchemy',
    'DB_SESSION': None,
    'SESSION_EXPIRY_SECONDS': 3600,  # Default session expiry
    'USE_REDIS_FOR_CQRS': False,
    'DELETE_EXPIRED_SESSIONS': False,
    'CSRF_REDIRECT_ON_FAILURE': True,
    'ENVIRONMENT': 'development',
}
