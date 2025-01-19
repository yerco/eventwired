import os
base_dir = os.path.dirname(os.path.abspath(__file__))

config = {
    'BASE_DIR': base_dir,
    'SECRET_KEY': '{app_name}_supersecretkey',
    'DATABASE_URL': 'sqlite+aiosqlite:///{app_name}.db',
    'STATIC_DIR': '{app_name}/static',  # User-defined static directory
    'STATIC_URL_PATH': '/static',  # User-defined static URL path
    'SESSION_EXPIRY_SECONDS': 7200,  # Extend session expiry to 2 hours
    'TEMPLATE_ENGINE': 'JinjaAdapter',
    'TEMPLATE_DIR': os.path.join(base_dir, 'templates'),
    'CSRF_REDIRECT_ON_FAILURE': True,
    'ENVIRONMENT': 'development',
    'CORS_ALLOWED_ORIGINS': ["*"],  # Beware, allowing all origins
}
