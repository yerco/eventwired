from demo_app.forms.register_form import RegisterForm
from src.event_bus import Event
from src.controllers.base_controller import BaseController

from demo_app.di_setup import di_container
from demo_app.models.user import User


async def register_controller(event: Event):
    controller = BaseController(event)

    form_service = await di_container.get('FormService')
    template_service = await di_container.get('TemplateService')
    orm_service = await di_container.get('ORMService')
    password_service = await di_container.get('PasswordService')

    request = event.data['request']
    http_method = request.method

    if http_method == "GET":
        context = {
            "form": RegisterForm(),
            "errors": {}
        }
        rendered_content = template_service.render_template('register.html', context)
        await controller.send_html(rendered_content)

    elif http_method == "POST":
        # Collect form data and ensure it's not stored as lists
        form_data = await request.form()

        # No need to manually clean the form data, it's handled in BaseForm
        form = await form_service.create_form(RegisterForm, data=form_data)
        is_valid, errors = await form_service.validate_form(form)

        if is_valid:
            password = password_service.hash_password(form.fields['password'].value)
            await orm_service.create(User, username=form.fields['username'].value, password=password)
            await controller.send_text("Registration successful!")
        else:
            # Render the form again with errors
            context = {"form": form, "errors": errors}
            rendered_content = template_service.render_template('register.html', context)
            await controller.send_html(rendered_content, status=400)
    else:
        await controller.send_error(405, "Method Not Allowed")
