import os
base_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    'BASE_DIR': base_dir,
    'SECRET_KEY': '{app_name}_supersecretkey',
    'DATABASE_URL': 'sqlite+aiosqlite:///{app_name}.db',
    'STATIC_DIR': '{app_name}/static',  # User-defined static directory
    'SESSION_EXPIRY_SECONDS': 7200,  # Extend session expiry to 2 hours
    'JWT_SECRET_KEY': 'my_secret_key',
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_SECONDS': 7200,  # 2 hours expiration time
    'ENVIRONMENT': 'development',
    'CORS_ALLOWED_ORIGINS': ["*"],  # Beware, allowing all origins
}