# Step 16: Authentication Service

In this step, we are introducing the AuthenticationService to handle user registration and login. This involves 
creating the necessary endpoints and services to ensure users can register with a username and password, and later
log in by verifying their credentials.

## Key Concepts

- `PasswordService`: Handles password hashing and validation. Registered as a transient service since it 
   doesn’t need to retain state.
- `AuthenticationService`: Handles user authentication. It interacts with the ORM to retrieve user data and uses
  `PasswordService` to verify the password. Also registered as a transient service, as each authentication request 
  can function independently.

## Service Registration

In `demo_app/di_setup.py`, we register the `PasswordService` and `AuthenticationService` as transient services, 
meaning they are re-instantiated each time they are used. This ensures a clean and stateless approach to authentication.

## Endpoint

We added `/register` and `/login` endpoints.
