# CSRF Protection: ENABLE_CSRF Configuration Flag

Cross-Site Request Forgery (CSRF) is a common vulnerability in web applications where an attacker tricks a user into performing actions they did not intend. CSRF protection is especially crucial when applications involve sensitive operations, like user authentication, profile updates, or transactions. For applications using frontend frameworks or libraries (e.g., React, Vue), secure communication between the frontend and backend requires CSRF protection.

To facilitate CSRF protection in our framework, we’ve introduced the configuration flag `ENABLE_CSRF`. This flag allows users to easily enable or disable CSRF protection according to their security requirements and frontend integration strategy.

## Rationale for ENABLE_CSRF

Modern web applications often rely on frontend JavaScript frameworks to handle the UI, making it essential to secure API calls sent from the frontend to the backend. Enabling or disabling CSRF protection can vary based on development needs, security requirements, and deployment phases (e.g., testing vs. production).

By creating `ENABLE_CSRF` as a configuration flag, we provide a flexible, centralized way to control CSRF protection throughout the application:

- Development Flexibility: Developers can disable CSRF for rapid prototyping or testing purposes without modifying the application’s middleware.
- Production Security: Enabling CSRF protection in production provides an additional security layer for user interactions with critical endpoints.

In the application’s configuration file, `ENABLE_CSRF` can be set to `True` or `False:
    
    ```python
    ENABLE_CSRF = True
    ```

## CSRF with Frontend Libraries

To ensure smooth integration with frontend libraries like React, Angular, or Vue, applications should follow these practices when ENABLE_CSRF is enabled:

1.	CSRF Token Management:
    - On the frontend, retrieve the CSRF token provided by the backend, usually set as a cookie or response header after login or an initial API call.
    - Include the CSRF token in request headers for state-changing actions.

2. Example in Javascript
    ```javascript
    const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken')).split('=')[1];

    fetch('/api/endpoint', {
        method: 'POST',
        headers: {
            'X-CSRF-Token': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ key: 'value' })
    });
    ```

3.	CSRF Header Requirement:
   - By default, the CSRF token should be sent in an HTTP header (e.g., X-CSRF-Token). The CSRF middleware will verify the token to authorize the request.


Note: HttpOnly and Secure flags are set in the CSRFMiddleware.


## Notes for development
- Need to improve XSS protection
- Could add more configurations flags and allow flexibility in CSRF handling, especially when integrating with a frontend library like React. Here’s how each setting contributes:
  1. `CSRF_COOKIE_NAME`: Defining the cookie name is useful for cases where the frontend reads the CSRF token from cookies, typically when you use libraries like Axios to manage CSRF tokens in requests.
  2. `CSRF_COOKIE_HTTPONLY`: Setting this to True makes the cookie inaccessible to JavaScript, enhancing security but preventing frontends from reading the token directly. Setting it to False gives frontend access, especially useful if you want React (or similar) to dynamically set headers.
  3. `CSRF_HEADER_NAME`: This defines the header where the token will be sent, which can be matched in the middleware. This flexibility is valuable for aligning with conventions or third-party libraries that may use specific header names.
  4. `CSRF_METHODS`: This defines which HTTP methods require CSRF checks, enabling customization depending on your security model.
