from src.dicontainer import di_container
from src.event_bus import EventBus

from src.models.base import Base
from src.services.https_redirect_middleware import HTTPSRedirectMiddleware
from src.services.orm.orm_service import ORMService
from src.services.form_service import FormService
from src.services.routing_service import RoutingService
from src.services.template_service import TemplateService
from src.services.security.authentication_service import AuthenticationService
from src.services.password_service import PasswordService
from src.services.middleware_service import MiddlewareService
from src.services.session_service import SessionService
from src.services.publisher_service import PublisherService

from src.middleware.logging_middleware import LoggingMiddleware
from src.middleware.timing_middleware import TimingMiddleware
from src.middleware.csrf_middleware import CSRFMiddleware
from src.middleware.session_middleware import SessionMiddleware

from demo_app.services.config_service import AppConfigService
from demo_app.subscriber_setup import register_subscribers

# Register services in the DI container
config_service = AppConfigService()
di_container.register_singleton(config_service, 'ConfigService')

di_container.register_transient(TemplateService, 'TemplateService')
di_container.register_transient(FormService, 'FormService')

event_bus = EventBus()
register_subscribers(event_bus)

di_container.register_singleton(event_bus, 'EventBus')

orm_service = ORMService(config_service=config_service, Base=Base)
di_container.register_singleton(orm_service, 'ORMService')

di_container.register_transient(PasswordService, 'PasswordService')
di_container.register_transient(AuthenticationService, 'AuthenticationService')

# Initialize the session service and register it
session_service = SessionService(orm_service=orm_service, config_service=config_service)
di_container.register_singleton(session_service, 'SessionService')

routing_service = RoutingService(event_bus=event_bus, config_service=config_service)
di_container.register_singleton(routing_service, 'RoutingService')

publisher_service = PublisherService(event_bus=event_bus)
di_container.register_singleton(publisher_service, 'PublisherService')

middleware_service = MiddlewareService()
middleware_service.register_middleware(SessionMiddleware(session_service), priority=10)
csrf_middleware = CSRFMiddleware()
middleware_service.register_middleware(csrf_middleware, priority=5)  # lower priority than session middleware
# HTTPS redirect middleware experimental
# https_redirect_middleware = HTTPSRedirectMiddleware(permanent=True)
# middleware_service.register_middleware(https_redirect_middleware, priority=10)

# middleware_service.register_middleware(LoggingMiddleware(), priority=0)
middleware_service.register_middleware(TimingMiddleware(), priority=1)
di_container.register_singleton(middleware_service, 'MiddlewareService')
