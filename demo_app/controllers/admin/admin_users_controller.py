from src.core.decorators import inject
from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event
from src.services.orm_service import ORMService
from src.services.template_service import TemplateService

from demo_app.decorators.requires_admin import requires_admin
from demo_app.models.user import User
from src.utils.paginator import Paginator


@requires_admin
@inject
async def admin_users_controller(event: Event, orm_service: ORMService, template_service: TemplateService):
    controller = HTTPController(event)
    request = event.data["request"]

    csrf_token = request.csrf_token
    raw_page = request.query_params.get("page", ["1"])
    if isinstance(raw_page, list):
        raw_page = raw_page[0]
    page = int(raw_page)

    total_users = await orm_service.count(User)
    paginator = Paginator(total_users, page, per_page=5)

    users = await orm_service.paginated(User, page=page, per_page=paginator.limit())

    context = {
        "users": users,
        "csrf_token": csrf_token,
        "page": paginator.page,
        "total_pages": paginator.total_pages,
        "pagination": paginator.to_dict()
    }
    rendered_content = template_service.render_template('admin/admin_users.html', context)
    await controller.send_html(rendered_content)


@requires_admin
@inject
async def admin_edit_user_controller(event: Event, orm_service: ORMService, template_service: TemplateService):
    controller = HTTPController(event, template_service)
    request = event.data["request"]
    user_id = int(event.data["path_params"]["id"])
    user = await orm_service.get(User, user_id)

    csrf_token = request.csrf_token# or session.data.get('csrf_token')

    if request.method == "GET":
        context = {
            "user": user,
            "csrf_token": csrf_token,
        }
        rendered = template_service.render_template("admin/admin_edit_user.html", context)
        await controller.send_html(rendered)

    elif request.method == "POST":
        form_data = await request.form()
        username_list = form_data.get("username", [])
        username = username_list[0] if username_list else ""
        is_admin = form_data.get("is_admin", ["off"])[0] == "on"
        await orm_service.update(User, user_id, username=username, is_admin=is_admin)
        await controller.send_redirect("/admin/users")


@requires_admin
@inject
async def admin_delete_user_controller(event: Event, orm_service: ORMService):
    request = event.data["request"]
    method = request.method

    controller = HTTPController(event)

    if method != "POST":
        await controller.send_error(405, "Method Not Allowed")
        return

    user_id = int(event.data["path_params"]["id"])
    await orm_service.delete(User, user_id)
    await controller.send_redirect("/admin/users")
