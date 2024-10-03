# CQRS
from src.services.orm.orm_service import ORMService

from demo_app.models.book import Book
from demo_app.di_setup import di_container


class BookCommandHandler:
    def __init__(self, orm_service: ORMService = None):
        self.orm_service = orm_service or di_container.get('ORMService')

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
        # Update the book record in the database using the title as the identifier value
        updated_book = await self.orm_service.update(Book, lookup_value=title, lookup_column="title", title=new_title, author=author, published_date=published_date, isbn=isbn, stock_quantity=stock_quantity)

        if updated_book:
            return f"Book titled '{title}' has been updated successfully."
        else:
            return f"Failed to update the book titled '{title}'."

    async def delete_book(self, title: str = None, author: str = None):
        if not title and not author:
            raise ValueError("At least one of 'title' or 'author' must be provided to delete a book.")

        # Attempt to delete the book based on title or author
        if title:
            deleted = await self.orm_service.delete(Book, lookup_value=title, lookup_column="title")
            if deleted:
                return f"Book with title '{title}' deleted successfully."

        if author:
            deleted = await self.orm_service.delete(Book, lookup_value=author, lookup_column="author")
            if deleted:
                return f"Books by author '{author}' deleted successfully."

        raise ValueError("No matching book found to delete.")


class BookQueryHandler:
    def __init__(self, orm_service: ORMService = None):
        self.orm_service = orm_service or di_container.get('ORMService')

    async def get_book_by_isbn(self, isbn: str):
        return await self.orm_service.get(Book, lookup_value=isbn, lookup_column="isbn")

    async def get_book_by_title(self, title: str):
        return await self.orm_service.get(Book, lookup_value=title, lookup_column="title")

    async def list_all_books(self):
        return await self.orm_service.all(Book)

    async def find_books_by_author(self, author: str):
        # Since there is no `filter` method, this will involve fetching all books and filtering manually
        all_books = await self.orm_service.all(Book)
        return [book for book in all_books if book.author == author]

    async def find_books_published_after(self, year: int):
        # Since there is no direct filtering, this will involve fetching all books and filtering manually
        all_books = await self.orm_service.all(Book)
        return [book for book in all_books if book.published_date and book.published_date.year > year]
