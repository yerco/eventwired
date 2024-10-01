from typing import TypeVar, Type

from src.event_bus import Event
from src.services.orm.orm_service import ORMService
from src.services.password_service import PasswordService
from src.services.template_service import TemplateService
from src.core.response import Response
from tests.test_di_container import ConfigService

T = TypeVar('T')


class AuthenticationService:
    def __init__(self, orm_service: ORMService, config_service: ConfigService):
        self.orm_service = orm_service
        self.config_service = config_service
        self.password_service = PasswordService()
        self.template_service = TemplateService(config_service=config_service)

    async def authenticate_user(self, User: Type[T], username: str, plain_password: str) -> T:
        user = await self.orm_service.get_by_column(User, column="username", value=username)
        if user and self.password_service.check_password(plain_password, user.password):
            return user
        return None

    async def send_unauthorized(self, event: Event):
        send = event.data.get('send')
        try:
            if send:
                # Render the template
                context = {"message": "Unauthorized: Please log in to access this page."}
                rendered_content = self.template_service.render_template('unauthorized.html', context)
                # Create the response object
                response = Response(content=rendered_content, status_code=401, content_type='text/html')
                # Cache-Control
                response.headers.append((b'Cache-Control', b'no-store, no-cache, must-revalidate, max-age=0'))
                # CSP
                response.headers.append((b'Content-Security-Policy', b"default-src 'self'"))
                # Strict-Transport-Security (HSTS): Enforce the use of HTTPS for future requests
                #response.headers.append((b'Strict-Transport-Security', b'max-age=63072000; includeSubDomains; preload'))
                # X-Content-Type-Options: Prevent the browser from trying to interpret files as a different MIME type than specified.
                response.headers.append((b'X-Content-Type-Options', b'nosniff'))
                # X-Frame-Options: Protect against clickjacking by preventing the page from being displayed in an iframe.
                response.headers.append((b'X-Frame-Options', b'DENY'))

                # Send the response using the response's send method
                await response.send(send)
        except Exception:  # TemplateNotFoundError:
            # Fallback to a default template if 'unauthorized.html' is not found
            rendered_content = """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Unauthorized Access</title>
                    <link rel="stylesheet" href="/static/css/style.css">
                </head>
                <body>
                    <h1>Unauthorized Access</h1>
                    <p>You do not have permission to view this page. Please log in to access it.</p>
                    <div>
                        <a href="/login">Login</a> | <a href="/register">Register</a>
                    </div>
                </body>
                </html>
            """
            response = Response(content=rendered_content, status_code=401, content_type='text/html')
            await response.send(send)
