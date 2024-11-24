import inspect
from typing import Dict, Type, Any


class DIContainer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DIContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self._services = {}
        self._singleton_instances = {}
        self._singleton_classes: Dict[str, Type] = {}
        self._transient_classes: Dict[str, Type] = {}
        self._transient_instances: Dict[str, Any] = {}
        self._scoped_instances = {}

    # Reset the DI container state
    def reset(self):
        self._services.clear()
        self._singleton_instances.clear()
        self._scoped_instances.clear()

    # Register a scoped service (shared within the same scope, e.g., within a request)
    def register_scope(self, class_type, scope, name=None):
        name = name or class_type.__name__
        if scope not in self._scoped_instances:
            self._scoped_instances[scope] = {}
        self._scoped_instances[scope][name] = class_type

    async def get_scoped(self, name, scope):
        if scope in self._scoped_instances and name in self._scoped_instances[scope]:
            return await self._create_instance(self._scoped_instances[scope][name])
        raise Exception(f"Scoped service {name} not found in scope {scope}")

    def register_singleton_class(self, class_type: Type, name: str = None):
        name = name or class_type.__name__
        self._singleton_classes[name] = class_type

    def register_singleton_instance(self, instance: Any, name: str = None):
        name = name or instance.__class__.__name__
        self._singleton_instances[name] = instance

    def register_transient_class(self, class_type: Type, name: str = None):
        name = name or class_type.__name__
        self._transient_classes[name] = class_type

    def register_transient_instance(self, instance: Any, name: str = None):
        name = name or instance.__class__.__name__
        self._transient_instances[name] = instance

    # Enhanced get method to support constructor injection (auto-wiring)
    async def get(self, name):
        # Check if it's a singleton instance
        if name in self._singleton_instances:
            return self._singleton_instances[name]

        # Check if it's a singleton class to instantiate
        if name in self._singleton_classes:
            instance = await self._create_instance(self._singleton_classes[name])
            self._singleton_instances[name] = instance
            return instance

        # Check if it's a transient class
        if name in self._transient_classes:
            instance = await self._create_instance(self._transient_classes[name])
            return instance

        # Check if it's a transient instance
        if name in self._transient_instances:
            return self._transient_instances[name]

        # Check if it's a scoped service
        # (Implement scoped retrieval if needed)

        raise Exception(f"Service {name} not found")

    # Synchronous get method to retrieve already instantiated services
    def get_sync(self, name):
        if name in self._singleton_instances:
            return self._singleton_instances[name]
        if name in self._transient_instances:
            return self._transient_instances[name]
        raise Exception(f"Service {name} not found or requires async initialization")

    async def _create_instance(self, class_type: Type):
        constructor = inspect.signature(class_type.__init__)
        dependencies = []

        for param in list(constructor.parameters.values())[1:]:
            param_type = param.annotation
            param_name = param.name

            if param_type == inspect._empty:
                # Attempt to resolve by parameter name
                if param_name in self._singleton_classes or param_name in self._services:
                    dependency = await self.get(param_name)
                    dependencies.append(dependency)
                elif param_name in self._transient_classes:
                    dependency = await self.get(param_name)
                    dependencies.append(dependency)
                elif param_name in self._transient_instances:
                    dependency = await self.get(param_name)
                    dependencies.append(dependency)
                elif param_name in self._singleton_instances:
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
