# Refactoring di_setup.py and Simplifications

## Original Setup

In the initial setup, the application required a user-defined user_startup_callback in `demo_app/app.py` to manually
configure services like `RoutingService`, static file routes, and custom routes. Additionally, `di_setup.py` had 
direct service registrations and explicit logic for the initialization of several services.

### demo_app/app.py

The `app.py` required the user to define a user_startup_callback for routing and static file setup:

```python
async def user_startup_callback(di_container):
    routing_service = await di_container.get('RoutingService')
    register_routes(routing_service)
    routing_service.setup_static_routes(static_dir="demo_app/static", static_url_path="/static")
```

### demo_app/di_setup.py

The `di_setup.py` file manually registered services, initialized the `RoutingService`, and had extensive
service setup logic.

## The Refactor

To simplify this process, we introduced the following concepts:

1. `@di_setup` Decorator

   - The `@di_setup` decorator registers service setup functions to be run during application startup. 
     Each decorated function is added to a registry and executed in the correct order.
   - This removes the need for explicit service initialization and registration in the user’s code. 
     Instead, the framework takes care of invoking these functions at the right time.

       ### Example of Using @di_setup:
    
       ```python
       @di_setup
       async def setup_routing_service(container):
           routing_service = RoutingService(event_bus=await container.get('EventBus'))
           await routing_service.start_routing()
           container.register_singleton(routing_service, 'RoutingService')
           await register_routes(routing_service)
       ```

2. `run_setups()`

    - The `run_setups()` function ensures all setup functions registered via `@di_setup` are executed during the 
      app startup, before processing any requests. This guarantees that all services are initialized properly, 
      abstracting this complexity away from the user.

## The Rationale

  - Simplicity: By using `@di_setup` and `run_setups()`, we avoid the need for a manual `user_startup_callback` 
                and reduce boilerplate in both `app.py` and `di_setup.py`.
  - Encapsulation: The framework manages service initialization, ensuring proper order and method calls, reducing 
                   user error and complexity.
  - Flexibility: Users still define their custom routes, but the rest of the setup is automated, making 
                 it easier to manage.

This refactor results in cleaner, more maintainable code while preserving the flexibility for user-specific logic.
