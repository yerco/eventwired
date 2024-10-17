import asyncio


# Helper to asynchronously initialize services or components.
# Accepts a factory function (which can be async) and its arguments.
async def async_init(factory_func, *args, **kwargs):
    # Ensure the function is called in an async context
    if asyncio.iscoroutinefunction(factory_func):
        instance = await factory_func(*args, **kwargs)
    else:
        instance = factory_func(*args, **kwargs)
    return instance
