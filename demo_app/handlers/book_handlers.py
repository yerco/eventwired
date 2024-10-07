# CQRS
from typing import Optional

from src.services.orm.orm_service import ORMService

from demo_app.models.book import Book
from demo_app.di_setup import di_container
from demo_app.models.book_read_model import BookReadModel

from src.services.redis_service import RedisService


class BookCommandHandler:
    def __init__(self, orm_service: ORMService = None, redis_service: Optional[RedisService] = None):
        self.orm_service = orm_service or di_container.get('ORMService')

        # Instantiate the read model if RedisService is available
        if redis_service:
            self.book_read_model = BookReadModel(redis_service)
        else:
            self.book_read_model = None

    async def add_book(self, title: str, author: str, published_date: str = None, isbn: str = None, stock_quantity: int = 0):
        try:
            # Convert stock_quantity from string to int, if necessary
            stock_quantity = int(stock_quantity) if isinstance(stock_quantity, str) else stock_quantity

            # Check for duplicate books by title and author
            existing_book = await self.orm_service.get(Book, lookup_value=title, lookup_column="title")
            if existing_book and existing_book.author == author:
                return {
                    "status": "error",
                    "message": "A book with this title and author already exists."
                }

            # Check ISBN uniqueness
            if isbn:
                existing_book_with_isbn = await self.orm_service.get(Book, lookup_value=isbn, lookup_column="isbn")
                if existing_book_with_isbn:
                    return {
                        "status": "error",
                        "message": "A book with this ISBN already exists."
                    }

            # Convert `published_date` to a proper date object if needed
            if published_date:
                try:
                    from datetime import datetime
                    published_date = datetime.strptime(published_date, "%Y-%m-%d").date()
                except ValueError:
                    return {
                        "status": "error",
                        "message": "Published date must be in the format YYYY-MM-DD."
                    }

            # If no errors, create the book
            new_book = await self.orm_service.create(
                Book,
                title=title,
                author=author,
                published_date=published_date,
                isbn=isbn,
                stock_quantity=stock_quantity
            )

            # Update the read model if Redis is enabled.
            # Note: In a full CQRS implementation, we would likely emit an event here
            # (e.g., BookCreatedEvent) and have a separate event handler or projection
            # service that listens for the event and updates the read model accordingly.
            # This pattern, known as "event sourcing", provides a complete history of state changes
            # and decouples the command side (write model) from the query side (read model).
            # However, for the purposes of this minimalistic example, we are directly updating
            # the read model after the command is executed.
            if self.book_read_model:
                await self.book_read_model.add_book(
                    title=title,
                    book_data={
                        "id": str(new_book.id),
                        "title": title,
                        "author": author,
                        "published_date": str(published_date) if published_date else None,
                        "isbn": isbn,
                        "stock_quantity": str(stock_quantity)
                    }
                )

            return {
                "status": "success",
                "message": f"Book '{title}' by {author} added successfully.",
                "book": new_book
            }
        except TypeError as e:
            # Handle specific type errors, like incorrect data types for fields
            print(f"TypeError while adding book: {str(e)}")
            return {
                "status": "error",
                "message": "There was an issue with the data types provided. Please check the input fields and try again."
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"An unexpected error occurred. Please try again later"
            }

    async def update_book(self, title: str, new_title: str, author: str, published_date: str = None, isbn: str = None, stock_quantity: int = 0):
        try:
            # Update the book record in the database using the title as the identifier value
            updated_book = await self.orm_service.update(
                Book,
                lookup_value=title,
                lookup_column="title",
                title=new_title,
                author=author,
                published_date=published_date,
                isbn=isbn,
                stock_quantity=stock_quantity,
                return_instance=True  # Ensure the ORM returns the updated book instance
            )

            if not updated_book:
                raise ValueError(f"Book with title '{title}' not found.")

            # Update the read model if Redis is enabled.
            # Note: In a full CQRS implementation, we would likely emit an event here
            # and have a separate event handler or projection
            # service that listens for the event and updates the read model accordingly.
            if self.book_read_model:
                await self.book_read_model.update_book(
                    title=new_title,
                    updated_data={
                        "id": str(updated_book.id),
                        "title": new_title,
                        "author": author,
                        "published_date": str(published_date) if published_date else None,
                        "isbn": isbn,
                        "stock_quantity": str(stock_quantity)
                    }
                )

            return True
        except ValueError as e:
            print(f"Validation error while updating book: {str(e)}")
            raise
        except Exception as e:
            # Handle unexpected errors
            print(f"Unexpected error while updating book: {str(e)}")
            raise  # Re-raise the exception to propagate it

    async def delete_book(self, title: str = None, author: str = None):
        try:
            if not title and not author:
                raise ValueError("At least one of 'title' or 'author' must be provided to delete a book.")

            deleted = False

            # Attempt to delete the book based on title or author
            if title:
                deleted = await self.orm_service.delete(Book, lookup_value=title, lookup_column="title")
                if not deleted:
                    raise ValueError(f"Book with title '{title}' not found.")
                if deleted and self.book_read_model:
                    await self.book_read_model.delete_book(title)

            if not deleted and author:
                deleted = await self.orm_service.delete(Book, lookup_value=author, lookup_column="author")
                if not deleted:
                    raise ValueError(f"Books by author '{author}' not found.")
                if deleted and self.book_read_model:
                    # Note: In a more complex scenario, we would need to iterate over books by this author.
                    await self.book_read_model.delete_book(author)

            if deleted:
                return {
                    "status": "success",
                    "message": f"Book with title '{title}' deleted successfully." if title else f"Books by author '{author}' deleted successfully."
                }

            return {
                "status": "error",
                "message": "No matching book found to delete."
            }

        except ValueError as e:
            print(f"Validation error while deleting book: {str(e)}")
            raise
        except Exception as e:
            # Handle unexpected errors
            # print(f"Unexpected error while deleting book: {str(e)}")
            raise Exception("An unexpected error occurred while deleting the book. Please try again later.")


# BookQueryHandler
# This class provides query operations for books, supporting a fallback mechanism.
# It first tries to use Redis as a read-optimized model to quickly retrieve the data.
# If Redis is not available or the data is not found, it falls back to using the relational database via the ORM service.
# In production CQRS systems, the preferred approach is to rely solely on the NoSQL read model to maximize read performance and scalability.
# However, this fallback mechanism is used here to ensure flexibility and to make the framework more accessible in different environments.
class BookQueryHandler:
    def __init__(self, orm_service: ORMService = None, redis_service: Optional[RedisService] = None):
        self.orm_service = orm_service or di_container.get('ORMService')

        # Instantiate the read model if RedisService is available
        if redis_service:
            self.book_read_model = BookReadModel(redis_service)
        else:
            self.book_read_model = None

    async def get_book_by_isbn(self, isbn: str):
        # Use Redis if available, otherwise fall back to the ORM
        if self.book_read_model:
            book = await self.book_read_model.get_book(isbn)
            if book:
                return book

        return await self.orm_service.get(Book, lookup_value=isbn, lookup_column="isbn")

    async def get_book_by_title(self, title: str):
        # Use Redis if available, otherwise fall back to the ORM
        if self.book_read_model:
            book = await self.book_read_model.get_book(title)
            if book:
                return book

        return await self.orm_service.get(Book, lookup_value=title, lookup_column="title")

    async def list_all_books(self):
        # Use Redis if available, otherwise fall back to the ORM
        if self.book_read_model:
            return await self.book_read_model.list_all_books()

        return await self.orm_service.all(Book)

    async def find_books_by_author(self, author: str):
        # Use Redis if available, otherwise fall back to the ORM
        if self.book_read_model:
            all_books = await self.book_read_model.list_all_books()
            return [book for book in all_books if book["author"] == author]

        # Since there is no `filter` method, this will involve fetching all books and filtering manually
        all_books = await self.orm_service.all(Book)
        return [book for book in all_books if book.author == author]

    async def find_books_published_after(self, year: int):
        # Use Redis if available, otherwise fall back to the ORM
        if self.book_read_model:
            all_books = await self.book_read_model.list_all_books()
            return [book for book in all_books if book.get("published_date") and int(book["published_date"].split("-")[0]) > year]

        # Since there is no direct filtering, this will involve fetching all books and filtering manually
        all_books = await self.orm_service.all(Book)
        return [book for book in all_books if book.published_date and book.published_date.year > year]
