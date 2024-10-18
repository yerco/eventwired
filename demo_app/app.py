from src.core.framework_app import FrameworkApp
from src.dicontainer import di_container
from src.core.setup_registry import run_setups

from demo_app.routes import register_routes


# Create the app, passing in the startup callback
async def app(scope, receive, send):
    try:
        # Run setup functions to initialize services before processing any requests
        await run_setups(di_container)
        routing_service = await di_container.get('RoutingService')
        # Custom route registration logic for the user app
        await register_routes(routing_service)
        # Create the app instance with the user-defined startup callback
        framework_app = FrameworkApp()
        # Delegate request handling to the framework_app instance
        await framework_app(scope, receive, send)
    except Exception as e:
        print(f"Error during app startup: {e}")
