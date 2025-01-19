from src.core.event_bus import EventBus
from src.models.base import Base
from src.services.orm_service import ORMService
from src.services.routing_service import RoutingService
from src.services.security.authentication_service import AuthenticationService
from src.services.password_service import PasswordService
from src.services.middleware_service import MiddlewareService
from src.services.session_service import SessionService
from src.services.publisher_service import PublisherService
from src.services.config_service import ConfigService
from src.services.jwt_service import JWTService

from src.middleware.cors_middleware import CORSMiddleware
from src.middleware.jwt_middleware import JWTMiddleware

from {app_name}.config import config as default_config
from {app_name}.subscriber_setup import register_subscribers


async def setup_container(container, config=None):
    container.register_singleton_instance(container, 'DIContainer')
    config_service = ConfigService(config or default_config)
    container.register_singleton_instance(config_service, 'ConfigService')

    event_bus = EventBus()
    await register_subscribers(event_bus)
    container.register_singleton_instance(event_bus, 'EventBus')

    await setup_services(container, config_service, event_bus)
    await setup_middleware(container, config_service, event_bus)

async def setup_services(container, config_service, event_bus):
    orm_service = ORMService(config_service=config_service, Base=Base)
    await orm_service.initialize()
    container.register_transient_instance(orm_service, 'ORMService')

    container.register_transient_class(PasswordService, 'PasswordService')
    auth_service = AuthenticationService(orm_service=orm_service, config_service=config_service)
    container.register_transient_instance(auth_service, 'AuthenticationService')
    jwt_service = JWTService(config_service=config_service)
    container.register_transient_instance(jwt_service, 'JWTService')
    session_service = SessionService(orm_service=orm_service, config_service=config_service)
    container.register_transient_instance(session_service, 'SessionService')
    publisher_service = PublisherService(event_bus=event_bus)
    container.register_transient_instance(publisher_service, 'PublisherService')

    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, jwt_service=jwt_service, config_service=config_service)
    await routing_service.initialize()
    container.register_transient_instance(routing_service, 'RoutingService')

async def setup_middleware(container, config_service, event_bus):
    # Middleware setup
    middleware_service = MiddlewareService(event_bus=event_bus)
    jwt_service = await container.get('JWTService')
    middleware_service.register_middleware(JWTMiddleware(jwt_service=jwt_service), priority=3)
    cors_middleware = CORSMiddleware(config_service=config_service)
    middleware_service.register_middleware(cors_middleware, priority=4)
    container.register_singleton_instance(middleware_service, 'MiddlewareService')
