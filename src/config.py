from src.services.config_service import ConfigService

config_service = ConfigService()
secret_key = config_service.get('SECRET_KEY')
prune_interval = config_service.get('PRUNE_INTERVAL')
database_url = config_service.get('DATABASE_URL')
