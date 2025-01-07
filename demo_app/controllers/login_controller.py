from http import HTTPStatus

from src.forms.login_form import LoginForm
from src.core.event_bus import Event, EventBus
from src.controllers.http_controller import HTTPController
from src.core.session import Session
from src.core.decorators import inject

from demo_app.models.user import User
from src.services.form_service import FormService
from src.services.security.authentication_service import AuthenticationService
from src.services.session_service import SessionService
from src.services.template_service import TemplateService


@inject
async def login_controller(event: Event, form_service: FormService, template_service: TemplateService,
                           auth_service: AuthenticationService, session_service: SessionService, event_bus: EventBus):

    controller = HTTPController(event, template_service)

    request = event.data['request']
    http_method = request.method
    session: Session = event.data.get('session')

    # Handle the GET request
    if http_method == "GET":
        # Render the login form (empty form initially)

        # Retrieve CSRF that was set in the middleware
        csrf_token = request.csrf_token or session.data['csrf_token']
        context = {
            "form": LoginForm(),  # Pass an empty form
            "errors": {},  # Pass empty errors dictionary
            "csrf_token": csrf_token,  # Pass the CSRF token from the middleware
        }
        rendered_content = template_service.render_template('login.html', context)
        await controller.send_html(rendered_content)

    # Handle the POST request
    elif http_method == "POST":
        form_data = await request.form()
        form = await form_service.create_form(LoginForm, data=form_data)
        is_valid, errors = await form_service.validate_form(form)

        # Ensure errors is a dictionary
        if errors is None:
            errors = {}

        if is_valid:
            username = form.fields['username'].value
            password = form.fields['password'].value

            # Use AuthenticationService to authenticate the user
            user = await auth_service.authenticate_user(User, username, password)

            if user:
                # Create a new session and store user information
                session = Session(session_id=None)  # Let it generate a new session ID
                event.data['session'] = session
                session.set('user_id', user.id)

                # Save session to the database
                await session_service.save_session(session.session_id, session.data)

                # Set the session ID in the response, so it can be sent in cookies
                event.data['set_session_id'] = session.session_id

                # Emit user.login.success event
                login_event = Event(name='user.login.success', data={'user_id': user.id})
                await event_bus.publish(login_event)

                context = {"user": user}
                rendered_content = template_service.render_template('welcome_after_login.html', context)
                await controller.send_html(rendered_content)
            else:
                # If the username doesn't exist or password is incorrect
                if 'login' not in errors:
                    errors['login'] = []
                errors['login'].append("Invalid username or password.")

                # Emit user.login.failure event
                login_event = Event(name='user.login.failure', data={'username': username})
                await event_bus.publish(login_event)

                context = {"form": form, "errors": errors}

                response = await controller.create_html_response(template='login.html', context=context, status=HTTPStatus.UNAUTHORIZED)
                await controller.send_response(response)
        else:
            # If form is invalid, render the form again with errors
            context = {"form": form, "errors": errors}
            response = await controller.create_html_response(template='login.html', context=context, status=400)
            await controller.send_response(response)

    else:
        # Invalid method handling
        await controller.send_error(405, "Method Not Allowed")
