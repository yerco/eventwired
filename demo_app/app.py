from src.core.framework_app import framework_app

from demo_app.routes import register_routes


# User-defined startup callback
async def user_startup_callback(di_container):
    routing_service = await di_container.get('RoutingService')

    if routing_service is None:
        raise ValueError("RoutingService is not configured properly")

    # Custom route registration logic for the user app
    register_routes(routing_service)

    # Set up static file routes with the user-provided static directory
    routing_service.setup_static_routes(static_dir="demo_app/static", static_url_path="/static")


# Create the app, passing in the startup callback
async def app(scope, receive, send):
    await framework_app(scope, receive, send, user_startup_callback=user_startup_callback)
