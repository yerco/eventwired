import os
base_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    'BASE_DIR': base_dir,
    'SECRET_KEY': 'supersecretkey',
    'DATABASE_URL': 'sqlite+aiosqlite:///demo_app.db',
    'USE_REDIS_FOR_CQRS': False,
    'SESSION_EXPIRY_SECONDS': 7200,  # Extend session expiry to 2 hours
    'TEMPLATE_ENGINE': 'JinjaAdapter',
    'TEMPLATE_DIR': os.path.join(base_dir, 'templates'),
    'JWT_SECRET_KEY': 'my_secret_key',
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_SECONDS': 7200,  # 2 hours expiration time
}
