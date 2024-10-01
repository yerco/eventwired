# Step 23: Authentication User Model

In this step, we improved the architecture of our authentication system and added more flexibility for developers.

## Changes Made

1. **Moved `send_unauthorized` from `RoutingService` to `AuthenticationService`**:
    - We refactored our framework to move the `send_unauthorized` function from `RoutingService` to
      `AuthenticationService` to adhere to the **Single Responsibility Principle (SRP)**.
    - This refactoring allows `AuthenticationService` to handle all aspects of user authentication, including
      rendering an unauthorized page if necessary.
    - The method now also supports rendering a custom unauthorized template (`unauthorized.html`).

2. **Template Requirement for Unauthorized Page**:
    - To allow a customizable unauthorized response, the framework requires the developer to define an
     `unauthorized.html` template in the `templates` folder.
    - This enables developers to provide a consistent and user-friendly unauthorized page, which can be easily customized.

3. **User Model Definition**:
    - Currently, the framework does **not provide a built-in `User` model**. Instead, we expect the developer 
      to define a custom `User` model.
    - A basic implementation of a `User` model could look like this:
   ```python
   class User(Base):
       __tablename__ = 'user'

       id = Column(Integer, primary_key=True, autoincrement=True)
       username = Column(String(50), nullable=False)
       password = Column(String(255), nullable=False)
    ```
    - The developer can define additional fields and methods as needed for their application.
