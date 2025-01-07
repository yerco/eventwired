from http import HTTPStatus

from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController
from src.core.session import Session
from src.core.decorators import inject

from demo_app.models.user import User
from demo_app.forms.register_form import RegisterForm
from src.services.form_service import FormService
from src.services.orm_service import ORMService
from src.services.password_service import PasswordService
from src.services.template_service import TemplateService


@inject
async def register_controller(event: Event, form_service: FormService, template_service: TemplateService,
                              orm_service: ORMService, password_service: PasswordService):
    controller = HTTPController(event)

    request = event.data['request']
    session: Session = event.data.get('session')
    http_method = request.method
    errors = {}

    if http_method == "GET":
        csrf_token = request.cookies.get('csrftoken', '') or session.data['csrf_token']
        # Render the registration form template for GET requests
        context = {
            "form": RegisterForm(),
            "errors": errors,
            "csrf_token": csrf_token,
        }
        rendered_content = template_service.render_template('register.html', context)
        await controller.send_html(rendered_content)

    elif http_method == "POST":
        # Collect form data and ensure it's not stored as lists
        form_data = await request.form()

        # Create form with the data and validate it
        form = await form_service.create_form(RegisterForm, data=form_data)
        is_valid, errors = await form_service.validate_form(form)

        user_exists = await orm_service.filter(User, lookup_value=form.fields['username'].value, lookup_column="username")
        if user_exists:
            errors = errors or {}
            errors['username'] = ["Username already exists."]

        if is_valid and not user_exists:
            # Hash the password and create the user
            password = password_service.hash_password(form.fields['password'].value)
            await orm_service.create(User, username=form.fields['username'].value, password=password)

            # Render the success page
            rendered_content = template_service.render_template('registration_success.html', {})
            await controller.send_html(rendered_content, status=HTTPStatus.CREATED)
        else:
            # Render the form again with errors for POST requests with invalid data
            context = {"form": form, "errors": errors}
            rendered_content = template_service.render_template('register.html', context)
            await controller.send_html(rendered_content, status=HTTPStatus.BAD_REQUEST)

    else:
        # Handle invalid HTTP methods
        await controller.send_error(405, "Method Not Allowed")
