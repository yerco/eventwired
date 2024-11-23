import re
import urllib.parse
from datetime import datetime
from urllib.parse import unquote

from src.core.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.di_setup import di_container
from demo_app.forms.book_form import BookForm
from demo_app.handlers.book_handlers import BookCommandHandler


async def commands_books_controller(event: Event):
    form_service = await di_container.get('FormService')
    template_service = await di_container.get('TemplateService')
    orm_service = await di_container.get('ORMService')
    try: # In queries_books_controller.py
        redis_service = await di_container.get('RedisService')
    except Exception as e:
        redis_service = None
    command_handler = BookCommandHandler(orm_service=orm_service, redis_service=redis_service)
    controller = HTTPController(event, template_service)

    # Request and path information
    request = event.data['request']
    http_method = request.method
    path = request.path

    # Patterns for different routes
    add_path_pattern = r"^/books/action/add$"
    edit_book_path_pattern = r"^/books/(?P<title>[^/]+)/edit$"
    delete_book_path_pattern = r"^/books/(?P<title>[^/]+)/delete$"

    # Add book (POST /books/action/add)
    if re.match(add_path_pattern, path) and http_method == "POST":
        form_data = await request.form()
        form = await form_service.create_form(BookForm, data=form_data)
        is_valid, errors = await form_service.validate_form(form)

        if is_valid:
            add_book_result = await command_handler.add_book(
                title=form.fields['title'].value,
                author=form.fields['author'].value,
                published_date=form.fields['published_date'].value,
                isbn=form.fields['isbn'].value,
                stock_quantity=form.fields['stock_quantity'].value
            )
            if add_book_result["status"] == "success":
                context = {"message": add_book_result["message"]}
                rendered_content = template_service.render_template('book_success.html', context)
            else:
                # Render form again with the error message if there's an error
                context = {
                    "form": form,
                    "errors": {"general": [add_book_result["message"]]},
                    "csrf_token": event.data['request'].csrf_token
                }
                rendered_content = template_service.render_template('book_add.html', context)

            await controller.send_html(rendered_content)
        else:
            context = {
                "form": form,
                "errors": errors,
                "csrf_token": event.data['request'].csrf_token
            }
            rendered_content = template_service.render_template('book_add.html', context)
            await controller.send_html(rendered_content)

    # Update book (PATCH /books/{title}/edit)
    elif re.match(edit_book_path_pattern, path) and http_method == "POST":
        form_data = await request.form()
        method_override = form_data.get('_method', [''])[0].upper()

        if method_override == "PATCH":
            match = re.match(edit_book_path_pattern, path)
            if match:
                # Decode the URL-encoded title
                title = urllib.parse.unquote(match.group('title'))
                form = await form_service.create_form(BookForm, data=form_data)
                is_valid, errors = await form_service.validate_form(form)
                # Convert published_date to a Python date object if it's provided
                published_date_str = form.fields['published_date'].value
                published_date = datetime.strptime(published_date_str, "%Y-%m-%d").date() if published_date_str else None
                if is_valid:
                    try:
                        updated_book = await command_handler.update_book(
                            title=title,
                            new_title=form.fields['title'].value,
                            author=form.fields['author'].value,
                            published_date=published_date,
                            isbn=form.fields['isbn'].value,
                            stock_quantity=form.fields['stock_quantity'].value
                        )
                        if updated_book:
                            context = {"message": f"Book titled '{title}' updated successfully."}
                            rendered_content = template_service.render_template('book_success.html', context)
                            await controller.send_html(rendered_content)
                    except ValueError:
                        await controller.send_error(404, "Book not found")
                    except Exception as e:
                        # Handle unexpected errors
                        await controller.send_error(500, f"Error updating book: Unexpected Error")  #: {str(e)}")
                else:
                    context = {
                        "form": form,
                        "errors": errors,
                        "csrf_token": event.data.get('csrf_token')
                    }
                    rendered_content = template_service.render_template('book_edit.html', context)
                    await controller.send_html(rendered_content)
        else:
            await controller.send_error(405, "Method Not Allowed")

    # Delete book (DELETE /books/{title}/delete)
    elif re.match(delete_book_path_pattern, path) and http_method == "POST":
        form_data = await request.form()
        method_override = form_data.get('_method', [''])[0].upper()

        if method_override == "DELETE":
            match = re.match(delete_book_path_pattern, path)
            if match:
                title = match.group('title')
                title = unquote(title)  # Decode '%20' to spaces
                try:
                    await command_handler.delete_book(title=title)
                    context = {"message": f"Book titled '{title}' deleted successfully."}
                    rendered_content = template_service.render_template('book_success.html', context)
                    await controller.send_html(rendered_content)
                except ValueError:
                    await controller.send_error(404, "Book not found")
        else:
            await controller.send_error(405, "Method Not Allowed")

    else:
        await controller.send_error(405, "Method Not Allowed")
