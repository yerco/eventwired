import re
import urllib.parse

from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event

from demo_app.di_setup import di_container
from demo_app.forms.book_form import BookForm
from demo_app.handlers.book_handlers import BookQueryHandler


async def queries_books_controller(event: Event):
    # Retrieve services from the DI container
    form_service = await di_container.get('FormService')
    template_service = await di_container.get('TemplateService')
    orm_service = await di_container.get('ORMService')
    try:
        redis_service = await di_container.get('RedisService')
    except Exception as e:
        print("Note: you are not using REDIS")
        redis_service = None

    # Instantiate Command and Query Handlers
    query_handler = BookQueryHandler(orm_service=orm_service, redis_service=redis_service)
    controller = HTTPController(event, template_service)

    request = event.data['request']
    http_method = request.method
    path = request.path

    # Patterns for different routes
    book_detail_path_pattern = r"^/books/(?P<title>[^/]+)$"
    # Pattern for the edit route
    edit_book_path_pattern = r"^/books/(?P<title>[^/]+)/edit$"
    add_path_pattern = r"^/books/action/add$"

    # List all books (GET /books)
    if path == "/books" and http_method == "GET":
        books = await query_handler.list_all_books()
        context = {
            "books": books,
            "csrf_token": event.data.get('csrf_token'),
        }
        rendered_content = template_service.render_template('book_list.html', context)
        await controller.send_html(rendered_content)

    if re.match(add_path_pattern, path) and http_method == "GET":
        # Create an empty form for the new book
        form = await form_service.create_form(BookForm, data={})

        # Set up the context for rendering
        context = {
            "form": form,
            "errors": {},  # No errors when initially rendering the form
            "csrf_token": event.data.get('csrf_token')  # CSRF token for form submission
        }

        # Render the template for adding a book
        rendered_content = template_service.render_template('book_add.html', context)
        await controller.send_html(rendered_content)

    # View details of a specific book (GET /books/{title})
    elif re.match(book_detail_path_pattern, path) and http_method == "GET":
        match = re.match(book_detail_path_pattern, path)
        if match:
            # Decode the title from URL encoding
            title = urllib.parse.unquote(match.group('title'))
            book = await query_handler.get_book_by_title(title)
            if not book:
                await controller.send_error(404, "Book not found")
            else:
                context = {
                    "book": book,
                    "csrf_token": event.data.get('csrf_token')
                }
                rendered_content = template_service.render_template('book_detail.html', context)
                await controller.send_html(rendered_content)

    # Show form for editing an existing book (GET /books/{title}/edit)
    if re.match(edit_book_path_pattern, path) and http_method == "GET":
        match = re.match(edit_book_path_pattern, path)
        if match:
            title = urllib.parse.unquote(match.group('title'))
            book = await query_handler.get_book_by_title(title)
            if not book:
                await controller.send_error(404, "Book not found")
            else:
                # Handle case where the book is a dictionary (from Redis) or an object (from ORM)
                if isinstance(book, dict):
                    book_data = {
                        "title": book.get("title"),
                        "author": book.get("author"),
                        "published_date": book.get("published_date") if book.get("published_date") else "",
                        "isbn": book.get("isbn"),
                        "stock_quantity": book.get("stock_quantity"),
                    }
                else:
                    book_data = {
                        "title": book.title,
                        "author": book.author,
                        "published_date": str(book.published_date) if book.published_date else "",
                        "isbn": book.isbn,
                        "stock_quantity": book.stock_quantity,
                    }

                # Create form using book data
                form = await form_service.create_form(BookForm, data=book_data)

                # Render the form with the book data
                rendered_content = template_service.render_template('book_edit.html', {
                    "form": form,
                    "errors": {},
                    "csrf_token": event.data.get('csrf_token')
                })
                await controller.send_html(rendered_content)
