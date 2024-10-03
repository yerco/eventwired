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
