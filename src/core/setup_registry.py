setup_registry = []

# Decorator to register a setup function for the DI container.
# These functions are collected and executed during the app's startup.
def di_setup(func):
    setup_registry.append(func)
    return func


# Run all setup functions registered with @di_setup.
# This should be called during the app's startup phase.
async def run_setups(container, config=None):
    # Run all setup functions registered with @di_setup
    for setup_fn in setup_registry:
        if config is not None:
            await setup_fn(container, config=config)
        else:
            await setup_fn(container)
