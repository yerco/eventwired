from contextvars import ContextVar


# Context variable for the current DI container
_current_container: ContextVar = ContextVar("current_container", default=None)


# Set the current DI container (e.g., during app or request lifecycle)
def set_container(container):
    if container is None:
        _current_container.set(None)  # Clear the context
        print("DI container cleared from context.")
    else:
        _current_container.set(container)
        print(f"DI container set in context: {container}")


# Get the current DI container. Raises an exception if none is set.
def get_container():
    container = _current_container.get()
    if not container:
        raise RuntimeError("No DI container is set in the current context.")
    print(f"DI container retrieved: {container}")
    return container
