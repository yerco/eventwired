from src.services.config_service import ConfigService
from src.core.event_bus import EventBus
from src.services.template_service import TemplateService
from src.services.form_service import FormService
from src.models.base import Base
from src.services.orm_service import ORMService
from src.services.security.authentication_service import AuthenticationService
from src.services.session_service import SessionService
from src.services.publisher_service import PublisherService
from src.services.websocket_service import WebSocketService
from src.services.routing_service import RoutingService

from src.services.middleware_service import MiddlewareService
from src.middleware.browser_session_middleware import BrowserSessionMiddleware
from src.middleware.csrf_middleware import CSRFMiddleware
from src.middleware.cors_middleware import CORSMiddleware

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
    container.register_transient_class(TemplateService, 'TemplateService')
    container.register_transient_class(FormService, 'FormService')

    orm_service = ORMService(config_service=config_service, Base=Base)
    await orm_service.initialize()
    container.register_transient_instance(orm_service, 'ORMService')

    auth_service = AuthenticationService(orm_service=orm_service, config_service=config_service)
    container.register_transient_instance(auth_service, 'AuthenticationService')

    session_service = SessionService(orm_service=orm_service, config_service=config_service)
    container.register_transient_instance(session_service, 'SessionService')

    publisher_service = PublisherService(event_bus=event_bus)
    container.register_transient_instance(publisher_service, 'PublisherService')

    # Delete if not needed
    container.register_singleton_class(WebSocketService, 'WebSocketService')

    routing_service = RoutingService(
        event_bus=event_bus,
        auth_service=auth_service,
        jwt_service=None,  # Placeholder for JWT service
        config_service=config_service,
    )
    await routing_service.initialize()
    container.register_transient_instance(routing_service, 'RoutingService')


async def setup_middleware(container, config_service, event_bus):
    # Middleware setup
    middleware_service = MiddlewareService(event_bus=event_bus)

    session_service = await container.get('SessionService')
    middleware_service.register_middleware(
        BrowserSessionMiddleware(session_service, config_service=config_service), priority=10
    )

    csrf_middleware = CSRFMiddleware(event_bus=event_bus, config_service=config_service)
    cors_middleware = CORSMiddleware(config_service=config_service)

    middleware_service.register_middleware(csrf_middleware, priority=9)  # Lower priority than session middleware
    middleware_service.register_middleware(cors_middleware, priority=4)

    container.register_singleton_instance(middleware_service, 'MiddlewareService')
