from src.core.dicontainer import DIContainer
from src.core.framework_app import FrameworkApp

from {app_name}.di_setup import setup_container
from {app_name}.routes import register_routes


container = DIContainer()

# Create the app, passing in the startup callback
async def app(scope, receive, send):
    try:
        await setup_container(container)
        # Create the app instance with the user-defined startup callback
        framework_app = FrameworkApp(container, register_routes)
        await framework_app.setup()
        # Delegate request handling to the framework_app instance
        await framework_app(scope, receive, send)
    except Exception as e:
        print(f"Error during app startup: {e}")
