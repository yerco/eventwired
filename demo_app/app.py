from src.core.dicontainer import DIContainer
from src.core.framework_app import FrameworkApp

from demo_app.di_setup import setup_container
from demo_app.routes import register_routes


# Create the app, passing in the startup callback
async def app(scope, receive, send):
    try:
        container = DIContainer()
        await setup_container(container)
        # Create the app instance with the user-defined startup callback
        framework_app = FrameworkApp(container, register_routes)
        await framework_app.setup()
        # Delegate request handling to the framework_app instance
        await framework_app(scope, receive, send)
    except Exception as e:
        print(f"Error during app startup: {e}")
