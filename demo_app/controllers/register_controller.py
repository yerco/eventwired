from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.di_setup import di_container
from demo_app.models.user import User
from demo_app.forms.register_form import RegisterForm


async def register_controller(event: Event):
    controller = HTTPController(event)

    # Retrieve the necessary services
    form_service = await di_container.get('FormService')
    template_service = await di_container.get('TemplateService')
    orm_service = await di_container.get('ORMService')
    password_service = await di_container.get('PasswordService')

    request = event.data['request']
    http_method = request.method

    if http_method == "GET":
        # Render the registration form template for GET requests
        context = {
            "form": RegisterForm(),
            "errors": {}
        }
        rendered_content = template_service.render_template('register.html', context)
        await controller.send_html(rendered_content)

    elif http_method == "POST":
        # Collect form data and ensure it's not stored as lists
        form_data = await request.form()

        # Create form with the data and validate it
        form = await form_service.create_form(RegisterForm, data=form_data)
        is_valid, errors = await form_service.validate_form(form)

        if is_valid:
            # Hash the password and create the user
            password = password_service.hash_password(form.fields['password'].value)
            await orm_service.create(User, username=form.fields['username'].value, password=password)

            # Render the success page
            rendered_content = template_service.render_template('registration_success.html', {})
            await controller.send_html(rendered_content)
        else:
            # Render the form again with errors for POST requests with invalid data
            context = {"form": form, "errors": errors}
            rendered_content = template_service.render_template('register.html', context)
            await controller.send_html(rendered_content, status=400)

    else:
        # Handle invalid HTTP methods
        await controller.send_error(405, "Method Not Allowed")
