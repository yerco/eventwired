from src.core.setup_registry import di_setup
from src.core.dicontainer import di_container
from src.core.event_bus import EventBus
from src.models.base import Base
from src.services.orm_service import ORMService
from src.services.form_service import FormService
from src.services.routing_service import RoutingService
from src.services.template_service import TemplateService
from src.services.security.authentication_service import AuthenticationService
from src.services.password_service import PasswordService
from src.services.middleware_service import MiddlewareService
from src.services.session_service import SessionService
from src.services.publisher_service import PublisherService
from src.services.websocket_service import WebSocketService
from src.services.factories import create_redis_service
from src.services.config_service import ConfigService
from src.services.jwt_service import JWTService

from src.middleware.timing_middleware import TimingMiddleware
from src.middleware.csrf_middleware import CSRFMiddleware
from src.middleware.session_middleware import SessionMiddleware

from demo_app.config import config
from demo_app.subscriber_setup import register_subscribers
# from demo_app.middleware.ip_geolocation_middleware import IpGeolocationMiddleware


@di_setup
async def setup_config_service(container):
    config_service = ConfigService(config)
    container.register_singleton(config_service, 'ConfigService')

# Just for the CQRS example at /books
@di_setup
async def setup_redis_service(container):
    redis_service = None
    config_service = await container.get('ConfigService')
    if config_service.get('USE_REDIS_FOR_CQRS'):
        redis_service = create_redis_service(critical=False)
        if redis_service:
            di_container.register_singleton(redis_service, 'RedisService')

@di_setup
async def setup_utility_service(container):
    di_container.register_transient(TemplateService, 'TemplateService')
    di_container.register_transient(FormService, 'FormService')

@di_setup
async def setup_event_bus(container):
    event_bus = EventBus()
    await register_subscribers(event_bus)
    di_container.register_singleton(event_bus, 'EventBus')

@di_setup
async def setup_orm_service(container):
    config_service = await container.get('ConfigService')
    orm_service = ORMService(config_service=config_service, Base=Base)
    await orm_service.initialize()
    di_container.register_singleton(orm_service, 'ORMService')

@di_setup
async def setup_services(container):
    config_service = await container.get('ConfigService')
    orm_service = await container.get('ORMService')
    event_bus = await container.get('EventBus')
    di_container.register_transient(PasswordService, 'PasswordService')
    auth_service = AuthenticationService(orm_service=orm_service, config_service=config_service)
    di_container.register_singleton(auth_service, 'AuthenticationService')
    jwt_service = JWTService(config_service=config_service)
    di_container.register_singleton(jwt_service, 'JWTService')
    session_service = SessionService(orm_service=orm_service, config_service=config_service)
    di_container.register_singleton(session_service, 'SessionService')
    publisher_service = PublisherService(event_bus=event_bus)
    di_container.register_singleton(publisher_service, 'PublisherService')
    websocket_service = WebSocketService()  # (event_bus=event_bus)
    di_container.register_singleton(websocket_service, 'WebSocketService')

@di_setup
async def setup_routing_service(container):
    event_bus = await container.get('EventBus')
    auth_service = await container.get('AuthenticationService')
    jwt_service = await container.get('JWTService')
    config_service = await container.get('ConfigService')
    routing_service = RoutingService(event_bus=event_bus, auth_service=auth_service, jwt_service=jwt_service, config_service=config_service)
    await routing_service.initialize()
    di_container.register_singleton(routing_service, 'RoutingService')

# Middleware setup
@di_setup
async def setup_middleware(container):
    middleware_service = MiddlewareService()
    session_service = await container.get('SessionService')
    middleware_service.register_middleware(SessionMiddleware(session_service), priority=10)
    csrf_middleware = CSRFMiddleware()
    middleware_service.register_middleware(csrf_middleware, priority=5)  # lower priority than session middleware
    # middleware_service.register_middleware(IpGeolocationMiddleware(), priority=0)
    middleware_service.register_middleware(TimingMiddleware(), priority=1)
    di_container.register_singleton(middleware_service, 'MiddlewareService')
