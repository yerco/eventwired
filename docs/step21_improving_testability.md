# Step 21: Improving Testability in the Framework

## Overview

In this step, we focus on improving the testability of the framework, with a special emphasis on the flow of 
the request, response, and middleware execution. Understanding the internals of how requests are processed 
in the **EDM ASGI Async** architecture is essential for writing effective and maintainable tests.

## Key Concepts

### 1. **Request Flow and the Role of the `Response` Class**

When a request is received, it is passed through the middleware layers, handled by the controller, and finally,
the response is sent back. The `Response` class plays a critical role in this flow. The `send` method of the
`Response` object is responsible for sending the actual HTTP response back to the client.

**Example of `Response.send`:**

```python
async def send(self, send):
    self._encode_content()  # Prepare the content
    await send({
        'type': 'http.response.start',
        'status': self.status_code,
        'headers': self.headers  # Headers, including cookies, are sent here
    })
    await send({
        'type': 'http.response.body',
        'body': self.body  # Send the body of the response
    })
```

### 2. Middleware Execution: The Role of MiddlewareService

The MiddlewareService manages the flow of the request and response through middleware layers. Each middleware 
can modify the request before it reaches the controller and modify the response before it is sent back.

Example of `MiddlewareService.execute`:
```python
    async def execute(self, event: Event, handler: Callable[[Event], None]) -> None:
        # Pass the event through all registered middlewares before reaching the handler
        for middleware, _ in self.middlewares:
            if hasattr(middleware, 'before_request'):
                event = await middleware.before_request(event)

        # Call the main handler (controller logic) after all middlewares have run
        await handler(event)

        # Pass the event and response back through the middlewares (after_request)
        for middleware, _ in reversed(self.middlewares):
            if hasattr(middleware, 'after_request'):
                await middleware.after_request(event)

        # Now, after all middlewares, send the response
        response = event.data.get('response')  # Fetch the response prepared by the controller
        if response:
            # Add response headers from the event data if available (including Set-Cookie)
            if 'response_headers' in event.data:
                for header in event.data['response_headers']:
                    response.headers.append(header)

            # Finally, send the response
            await response.send(event.data['send'])
```

The execute method ensures that:

- Before the Request: Middleware can modify the incoming request (e.g., authentication, validation).
- After the Controller: Middleware can modify the outgoing response (e.g., headers, cookies).
- Sending the Response: After all modifications, the `Response.send` method is invoked to send the response 
  back to the client.

### 3. Testability Considerations

To improve testability, especially when testing controllers or middleware interactions, we mock the behavior 
of `send`, `Response.send`, and `MiddlewareService.execute`. This allows us to simulate request/response cycles
and verify that middleware and controller logic behave as expected without sending actual HTTP responses.

In test cases, it's good to have in mind:
- Mock the send method in the `Response` class to verify that responses are properly generated.
- Simulate the `MiddlewareService.execute` flow to track how middlewares handle requests and responses.
- Use `AsyncMock` for any asynchronous methods to avoid NoneType errors during testing.

By decoupling the logic and following these principles, we can maintain a clear separation of concerns, 
which helps simplify the testing process.

## Publisher
In this step we added the `Publisher` class to the framework, which is responsible for publishing events to the
event bus. This class provides a simple interface for publishing events and allows us to test event-driven 
functionality more easily.

## Testing Recommendations and Explanations

In this step, we introduced various approaches to testing, demonstrating how to balance between unit tests,
hybrid tests, and integration tests. The tests are placed in three separate files for clarity:

- **Unit Tests**: `demo_app/tests/test_login_controller_unit.py`
- **Integration Tests**: `demo_app/tests/integration/test_login_controller_integration.py`
- **Hybrid Tests**: `demo_app/tests/hybrid/test_login_controller_hybrid.py`

### 1. **Unit Test: `test_login_controller_post_success`**
- **File**: `test_login_controller_unit.py`
- **Nature**: This is a **pure unit test**, where we mock all the external dependencies 
  (e.g., form service, authentication service). The focus is on testing the controller logic in isolation, 
  ensuring that the expected flow (e.g., form validation, session creation) occurs as intended.
- **Key Points**:
  - **Fast execution** because everything is mocked.
  - **Clear dependencies**: The developer needs to know exactly what to mock, making it critical to have 
    a clear map of the controller's dependencies.
  - **Drawbacks**: It doesn't test how the real services behave, so there’s limited confidence in full 
    system correctness.

### 2. **Integration Test: `test_login_controller_post_success_full`**
- **File**: `test_login_controller_integration.py`
- **Nature**: This is a **full integration test**, where the real ORMService is used, and the database is actually
  accessed. It simulates a full login process, storing and retrieving data from the database.
- **Key Points**:
  - **High confidence** that the system works in a real environment since it tests real services.
  - **Slower**: The test involves real database access, making it slower compared to unit tests.
  - **Recommendation**: This test is useful for ensuring the entire login flow works as expected but can become 
    slower as the system grows. It’s ideal for ensuring the correctness of critical flows.

### 3. **Hybrid Test: `test_login_controller_post_success_hybrid_using_real_orm`**
- **File**: `test_login_controller_hybrid.py`
- **Nature**: This test is **hybrid** because it uses the real ORMService, but mocks other components 
  like the form service and event bus. It provides a balance between full integration and unit testing 
  by focusing on some real components while mocking others.
- **Key Points**:
  - **Flexibility**: You can choose which services to mock and which to keep real.
  - **Balanced execution time**: Faster than full integration tests but provides more confidence than pure unit tests.
  - **Drawbacks**: Requires careful design to ensure important components are being tested appropriately.

### General Recommendations

- **Testing with Real Container**:
  - Using the real DI container in tests provides confidence that the system works as expected in real scenarios.
    However, it comes with **drawbacks**:
    - **Complexity**: The test setup becomes more complex, especially when you need to manage real services
      (e.g., database connections, event bus).
    - **Speed**: Tests can slow down significantly as real components (like databases) are involved.
  - **When to Use**: It's recommended for integration or system-level testing but avoid using the real container
    in unit tests unless absolutely necessary.

- **Mocking for Unit Tests**:
  - In unit tests, it's essential to have a **clear understanding of the dependencies** the controller is using,
    so you can mock them effectively. This allows you to isolate the logic under test and verify behaviors in
    specific scenarios without needing to rely on the real services.

By providing a mix of unit, hybrid, and integration tests, we ensure coverage at various levels of the application. 
Each type of test serves a distinct purpose, helping to balance test speed, coverage, and confidence in the system.

### Note on Integration Tests

From a development perspective, **integration tests** tend to be **faster to write** compared to unit tests 
because they do not require mocking and stubbing every dependency. By using the real services and components,
the test setup becomes more straightforward. However, while integration tests provide confidence in how the
system works as a whole, they may execute more slowly than unit tests due to interactions with
real components like databases.

For developers who want quicker feedback during development and testing, integration tests can be a great
starting point. That said, they should still be balanced with unit tests and hybrid tests for more granular
control and faster test execution in larger systems.
