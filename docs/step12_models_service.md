# Step 12: Implementing the Models Service with Dependency Injection (DI)

In this step, we integrated a **Models Service** into the framework to manage model registration and interaction
with different ORMs (SQLAlchemy, Tortoise). We also added support for a **Dependency Injection (DI) Container** to
manage services and auto-wiring, making the system modular, scalable, and decoupled.

## Overview

The **Models Service** is responsible for loading, registering, and interacting with models across different ORMs.
We added flexibility by enabling support for both **SQLAlchemy** and **Tortoise ORM**, allowing users to switch 
between these ORM solutions based on their needs.

Additionally, a **DI Container** was implemented to simplify the injection of dependencies, ensuring that each
service and model is easily accessible while reducing tight coupling between different components.

---

## 1. Models Service

The **Models Service** allows you to register models dynamically, either through modules or directories. Here's a summary of its key functionality:

- **Registration**: Models can be registered individually or loaded from directories or modules.
- **ORM Support**: The service supports both SQLAlchemy and Tortoise ORM models.
- **ORM Initialization**: During application startup, the ORM initializes models and manages database schema creation.

### Key Methods

- `register_model`: Registers a model with a given name.
- `load_models_from_module`: Dynamically loads models from a specified module.

## 2. Dependency Injection (DI) and Auto-Wiring

A **Dependency Injection Container** was introduced to manage the lifecycle of various services and models. 
This simplifies service access and ensures each service (like ORM, EventBus, or Routing) is initialized only once,
unless explicitly configured otherwise.

### Features of the DI Container

- Singleton Management: Registers singleton services that maintain state across the entire application lifecycle.
- Transient Services: Registers services that create a new instance each time they are requested.
- Auto-Wiring: Automatically resolves and injects dependencies based on constructor arguments, simplifying service
  registration and retrieval.

#### Example DI Container Usage
1. Singleton Registration:
    ```python
    di_container.register_singleton(orm_service, 'ORMService')
    ```

2. Transient Registration:
    ```python
    di_container.register_transient(TemplateService)
    ```

3. Auto-Wiring Example:
    ```python
   template_service = di_container.get('TemplateService')
    ```

## 3. Application Integration

We updated the main application entry point to make use of the DI container. Here’s an overview of how services
and models are injected and initialized in the app:

### Application Initialization

During startup, the ORM service is initialized, and models are registered dynamically:
    ```python
    orm_service = di_container.get('ORMService')async def startup():
    orm_service = di_container.get('ORMService')
    user_model = di_container.get('UserModel')
    await orm_service.init([user_model])
    ```

### Event Handling

When an HTTP request is received, the application publishes an event that is picked up by the **EventBus**, 
enabling decoupled event-driven interactions.
    ```python
    event = Event(name='http.request.received', data=event_data)
    await event_bus.publish(event)
    ```

---

## Conclusion

This step introduced a flexible Models Service and integrated a DI Container to make the framework more
modular and scalable. By leveraging auto-wiring, we reduced the complexity of manually managing service
dependencies. As you continue developing, these patterns will enable  to build highly decoupled and maintainable
applications.

The next step will likely involve refining the architecture further and ensuring that the system is ready
for scenarios like authorization, authentication, and multi-environment deployments.

Note that as this is experimental I'll have to check if it works as expected and if it's a good idea to keep it. 
