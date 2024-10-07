Here's a markdown document that summarizes the use of CQRS in your framework:

```markdown
# Step 24: Implementing CQRS in the Framework

## Introduction to CQRS

Command Query Responsibility Segregation (CQRS) is an architectural pattern that separates the operations that modify
data (commands) from the operations that read data (queries). This pattern is particularly useful in applications
that require scalability or have complex business logic, ensuring that reads and writes are handled independently.

In our implementation, **commands** are responsible for **Create, Update, Delete (CUD)** operations, while
**queries** handle **Read (R)** operations.

For our educational framework, we've applied CQRS to the `/books` endpoint as a demo. Given the simplicity
of this example, using CQRS here may be overkill. However, it provides a good learning exercise for understanding
the pattern and how to structure an application using CQRS principles.

## Implementation in the Books Endpoint

### Commands: `/books/action`
- **Add Book**: Adds a new book to the database.
  - **Route**: `POST /books/action/add`
  - **Handler**: A command handler (`BookCommandHandler`) that performs a `create` operation for new books.

- **Update Book**: Edits an existing book by title.
  - **Route**: `PATCH /books/{title}/edit`
  - **Handler**: Updates a book by using command logic to modify attributes.

- **Delete Book**: Deletes a book by title.
  - **Route**: `DELETE /books/{title}/delete`
  - **Handler**: Deletes an existing book by using a command handler.

### Queries: `/books`
- **List All Books**: Lists all the books in the database.
  - **Route**: `GET /books`
  - **Handler**: A query handler (`BookQueryHandler`) retrieves all books.

- **Get Book Details**: Displays detailed information about a specific book.
  - **Route**: `GET /books/{title}`
  - **Handler**: Uses a query handler to fetch a book by its title.

- **Show Edit Form for Book**: Displays a form to edit a book's details.
  - **Route**: `GET /books/{title}/edit`
  - **Handler**: Uses a query handler to get the book and return an edit form.

## Key Considerations
- **Overkill for Small Applications**: CQRS introduces complexity by splitting the read and write logic. For simple CRUD operations (such as in our `/books` endpoint), this separation might be excessive. However, for applications with more complex business requirements or scalability needs, CQRS can be extremely beneficial.

- **Benefits**: The separation of commands and queries allows for optimized scaling of read and write operations independently. This can be helpful for complex microservices or event-driven architectures.

## Most Important Parts of the Code

1. **Command Handlers**:
   - `BookCommandHandler` contains logic for adding, updating, and deleting books.

   ```python
   async def add_book(self, title: str, author: str, ...):
       # Create a new book after performing validation
       await self.orm_service.create(Book, ...)
   ```

2. **Query Handlers**:
   - `BookQueryHandler` retrieves book information.

   ```python
   async def list_all_books(self):
       # Retrieve all books
       return await self.orm_service.all(Book)
   ```

3. **Route Configuration**:
   - Commands and queries are mapped to different routes in `commands_books_controller` and `queries_books_controller`.

## Using `OrmService` in CQRS Context

The `OrmService` provides an interface for handling CRUD operations and simplifies database interactions. 
Below is a quick reference guide for developers on how to use the `OrmService` within the CQRS context.

### Initialization

To initialize `OrmService`, you need to set up the database configuration:

```python
from src.services.orm.orm_service import ORMService
from src.services.config_service import ConfigService

config_service = ConfigService()
orm_service = ORMService(config_service)
await orm_service.init('my_database.db')
```

### Basic CRUD Operations

1. Create
To create a new record in the database:
    
    ```python
   from demo_app.models.book import Book

    new_book = await orm_service.create(
        Book,
        title="A New Book",
        author="Author Name",
        published_date="2024-01-01",
        isbn="1234567890",
        stock_quantity=10
    )
    ```

2. Get by Primary Key or Specific Column
   To retrieve an instance by primary key or another specific column:
   
    ```python
   # Get by primary key (default column is 'id')
   book = await orm_service.get(Book, lookup_value=1)
   
   # Get by a specific column (e.g., 'title')
   book = await orm_service.get(Book, lookup_value="A New Book", lookup_column="title")
    ```

3. Update by Primary Key or Specific Column
   To update an instance by its primary key or a different column:
   
    ```python
   # Update by primary key (id) and return the updated instance
   updated_book = await orm_service.update(
    Book,
    lookup_value=1,
    lookup_column="id",
    title="Updated Book Title",
    return_instance=True  # Optional, to return the updated instance
   )
   
   # Update by specific column (e.g., 'title')
   updated_book = await orm_service.update(
    Book,
    lookup_value="A New Book",
    lookup_column="title",
    author="Updated Author",
    return_instance=True
   )
    ```

4. Delete by Primary Key or Specific Column
   To delete an instance from the database:
    
   ```python
   # Delete by primary key (default column is 'id')
   await orm_service.delete(Book, lookup_value=1)

   # Delete by a specific column (e.g., 'title')
   await orm_service.delete(Book, lookup_value="Updated Book Title", lookup_column="title")
   ```

5. Retrieve All Records
    To retrieve all records from a table:
    
     ```python
     books = await orm_service.all(Book)
     ```

## Implementing CQRS with Redis

As this is an effort for educational purposes we implemented the Command Query Responsibility Segregation (CQRS) pattern. 
The implementation involved splitting the write (commands) and read (queries) operations,
leveraging Redis to optimize reads, while still supporting fallback to our traditional ORM when Redis is not available.

## Using Redis for CQRS

For the query side, we opted to use Redis to enhance read performance. Redis is a great fit due to its low 
latency and ability to quickly handle large amounts of read requests, especially compared to traditional databases.
We utilized the `BookReadModel` class to handle read-related operations by storing data in Redis.

If Redis is not available (either because it isn't configured or it cannot connect), our implementation falls
back to using the ORM service for reads. This ensures that the system remains functional even if Redis is
offline or unavailable. We provided the `RedisService` class with a `critical` parameter, allowing us to
decide whether the absence of Redis should be a fatal error or gracefully handled with a fallback.

## Simplification and Event Sourcing

Although CQRS often goes hand-in-hand with Event Sourcing, we decided to simplify our implementation for now
by directly updating the read model after a command is executed. In a full event-driven system, 
commands would emit events (e.g., `BookCreatedEvent`), and these events would be processed by separate services
(projections) to update read models. By avoiding this complexity, our implementation is easier to understand
and maintain, while still demonstrating the core concept of CQRS.

This approach also means that we are not maintaining a complete history of changes (as we would with Event Sourcing).
Instead, the read model is simply kept in sync after each command. While this is sufficient for many use cases,
adopting Event Sourcing in the future would add capabilities such as reconstructing historical state and 
auditing all changes over time.

## Fallback to ORM for Queries

To ensure reliability and continuity, we included a fallback mechanism to the ORM for all queries when Redis 
is not available. This fallback mechanism allows the application to continue functioning without Redis, 
albeit with a potential performance cost. This strategy is particularly useful for development environments, 
or situations where Redis might be temporarily unavailable. It is also a good illustration of a resilient CQRS 
implementation, which can adapt to varying infrastructure conditions.

## Summary

- **CQRS Implementation**: Commands and queries were separated, with Redis used for the read model to enhance performance.
- **Event Sourcing Simplification**: We directly update the read model after commands, avoiding the complexity of
  event-driven projections for now.
- **Redis Fallback**: When Redis is unavailable, the system gracefully falls back to the traditional ORM for read operations.
