import inspect


class DIContainer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DIContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._services = {}
        self._singletons = {}

    # Register a singleton object, multiple instances of the same class can be registered using different names
    def register_singleton(self, instance, name=None):
        name = name or instance.__class__.__name__
        self._singletons[name] = instance

    # Register a transient object (new instance every time)
    def register_transient(self, class_type, name=None):
        name = name or class_type.__name__
        self._services[name] = class_type

    # Enhanced get method to support constructor injection (auto-wiring)
    async def get(self, name):
        if name in self._singletons:
            return self._singletons[name]
        elif name in self._services:
            return await self._create_instance(self._services[name])
        raise Exception(f"Service {name} not found")

    async def _create_instance(self, class_type):
        constructor = inspect.signature(class_type.__init__)
        dependencies = []

        # # If the class has no dependencies, just instantiate it
        # if len(constructor.parameters) == 1:  # Only 'self' is in parameters
        #     return class_type()

        for param in list(constructor.parameters.values())[1:]:
            param_type = param.annotation
            param_name = param.name

            if param_type == inspect._empty:
                # Try to resolve by parameter name if no annotation is present
                if param_name in self._singletons or param_name in self._services:
                    dependency = await self.get(param_name)
                    dependencies.append(dependency)
                elif param.default != param.empty:
                    dependencies.append(param.default)
                else:
                    raise Exception(f"Cannot resolve dependency '{param_name}' for class {class_type.__name__}")
            elif param_type in [str, int, float, bool]:
                if param.default != param.empty:
                    dependencies.append(param.default)
                else:
                    raise Exception(f"Cannot resolve primitive type dependency '{param_name}' for class {class_type.__name__}")
            else:
                dependency_name = param_type.__name__
                dependency = await self.get(dependency_name)
                dependencies.append(dependency)

        instance = class_type(*dependencies)
        return instance


di_container = DIContainer()
