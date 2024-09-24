# Step 11: ORM Service Integration

In this step, we introduce a new component to the framework: the `ORMService`. This service is designed to
provide an abstraction layer over different ORM tools, namely SQLAlchemy and Tortoise ORM. 
The primary role of `ORMService` is to handle database interactions such as table creation, CRUD operations, 
and initialization for both SQLAlchemy and Tortoise database engines.

## Key Components

### Initialization
The `ORMService` dynamically selects the ORM engine based on the configuration, either SQLAlchemy or Tortoise, 
and manages the setup accordingly. The initialization process includes setting up the database connection and 
creating the necessary database tables. The models should be given as an input.

- **SQLAlchemy**:
  The service creates an SQLAlchemy engine and sets up the database tables using a declarative base.

- **Tortoise ORM**:
  The service initializes Tortoise ORM, connects it to the configured database, and generates the necessary schemas.

### CRUD Operations
The `ORMService` provides basic CRUD (Create, Read, Update, Delete) functionality through the adapter pattern.
It delegates the actual database operations to the respective ORM adapter (`SQLAlchemyAdapter` or `TortoiseAdapter`),
making it easy to switch between ORMs without changing the core application logic.

### Cleanup
At the end of the application's lifecycle, `ORMService` ensures proper cleanup of database connections.

### Example Usage

```python
# Initialize ORM with models
await orm_service.init(models=[UserModel, ProductModel])

# Perform CRUD operations
new_user = await orm_service.create(UserModel, username="testuser", email="test@example.com")
user = await orm_service.get(UserModel, identifier=new_user.id)
await orm_service.update(UserModel, identifier=user.id, email="newemail@example.com")
await orm_service.delete(UserModel, identifier=user.id)
```

## Abandoning the Service Manager

Initially, I considered creating a `ServiceManager` to handle various services (there's a branch oon that following
that direction which then gave birth to a dependency injection initiative :P ). However, I abandoned that approach 
to avoid creating a “God Object” — a design where a single object handles too many responsibilities, 
leading to poor maintainability and scalability. Instead, by keeping services like ORMService decoupled,
the framework maintains separation of concerns, ensuring that each component remains focused and easier to manage.
