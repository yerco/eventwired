from {app_name}.controllers.home_controller import home_controller


async def register_routes(routing_service):
    routing_service.add_route('/', 'GET', home_controller)
