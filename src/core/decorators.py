import inspect
from functools import wraps

from src.core.context_manager import get_container


# Resolve a service by name using the current DI container context.
def resolve(service_name: str):
    container = get_container()
    return container.get(service_name)


# Decorator to automatically inject dependencies into a function's parameters.
# Dependencies are resolved using the DI container.
def inject(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        print(f"Injecting dependencies for {func.__name__}...")
        container = get_container()
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name in kwargs or name in sig.bind_partial(*args).arguments:
                continue  # Skip already provided arguments
            if param.annotation != inspect._empty:
                service_name = param.annotation.__name__
                print(f"Resolving {service_name} for {func.__name__}")
                dependency = await container.get(service_name)
                kwargs[name] = dependency
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        container = get_container()
        sig = inspect.signature(func)
        for name, param in sig.parameters.items():
            if name in kwargs or name in sig.bind_partial(*args).arguments:
                continue  # Skip already provided arguments
            if param.annotation != inspect._empty:
                service_name = param.annotation.__name__
                dependency = container.get_sync(service_name)  # Use sync retrieval for sync functions
                kwargs[name] = dependency
        return func(*args, **kwargs)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
