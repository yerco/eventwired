from {app_name}.controllers.api_login_controller import api_create_user_controller, api_login_controller, api_protected_controller


async def register_routes(routing_service):
    routing_service.add_route('/api/create', ['POST'], api_create_user_controller)
    routing_service.add_route('/api/login', ['POST'], api_login_controller)
    routing_service.add_route('/api/protected', ['GET'], api_protected_controller, requires_jwt_auth=True)
