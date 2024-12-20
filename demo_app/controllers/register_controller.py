from http import HTTPStatus

from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.di_setup import di_container
from demo_app.models.user import User
from demo_app.forms.register_form import RegisterForm
from src.core.session import Session


async def register_controller(event: Event):
    controller = HTTPController(event)

    # Retrieve the necessary services
    form_service = await di_container.get('FormService')
    template_service = await di_container.get('TemplateService')
    orm_service = await di_container.get('ORMService')
    password_service = await di_container.get('PasswordService')

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
