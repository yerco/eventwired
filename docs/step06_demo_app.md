# Step 06: Creating a Demo App

## Overview

In this step, we refactored our project to create a small `demo_app` that demonstrates how to 
use the framework while keeping user code separate from the framework's core logic. 
This ensures a clean separation of concerns and makes it easy to extend and customize the application.

## Key Changes

### 1. `demo_app/app.py`

We created `demo_app/app.py` as the entry point for the demo application. 
This file initializes the core services from the framework (such as `EventBus` and `RoutingService`) 
and links them to the custom `ControllersService` defined within the `demo_app`.

### 2. Extending `ControllersService`

In `demo_app/services/controllers_service.py`, we extended the framework's `ControllersService` to
implement specific route handling for the demo app. This demonstrates how easy it is to add custom 
functionality to the application while relying on the core framework for foundational services.

### 3. Decoupling User Code from Framework Code

By placing the custom `ControllersService` and application logic within `demo_app`, we clearly 
separate user-defined behavior from the underlying framework. This structure not only promotes 
better code organization but also makes it easier to maintain and scale the application.

## Conclusion

This small step showcases how to build a custom application using the framework with minimal setup.
The user only needs to extend the `ControllersService` and implement specific route handlers,
while the framework handles the rest.
