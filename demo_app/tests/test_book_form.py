import pytest
from datetime import date, timedelta
from demo_app.forms.book_form import BookForm


@pytest.mark.asyncio
async def test_book_form_valid_data():
    # Valid data
    data = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "published_date": "2008-08-01",
        "isbn": "9780132350884",
        "stock_quantity": 10
    }
    form = BookForm(data=data)
    is_valid = await form.is_valid()
    assert is_valid is True
    assert form.get_errors() == {}


@pytest.mark.asyncio
async def test_book_form_missing_required_fields():
    # Missing required fields: title and author
    data = {
        "published_date": "2008-08-01",
        "isbn": "9780132350884",
        "stock_quantity": 10
    }
    form = BookForm(data=data)
    is_valid = await form.is_valid()
    assert is_valid is False
    assert "title" in form.get_errors()
    assert "author" in form.get_errors()


@pytest.mark.asyncio
async def test_book_form_invalid_published_date_format():
    # Invalid date format for `published_date`
    data = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "published_date": "08-01-2008",  # Incorrect format
        "isbn": "9780132350884",
        "stock_quantity": 10
    }
    form = BookForm(data=data)
    is_valid = await form.is_valid()
    assert is_valid is False
    assert "published_date" in form.get_errors()
    assert form.get_errors()["published_date"] == ["Enter a valid date in YYYY-MM-DD format."]


@pytest.mark.asyncio
async def test_book_form_published_date_in_future():
    # Future published date
    future_date = (date.today() + timedelta(days=10)).isoformat()
    data = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "published_date": future_date,
        "isbn": "9780132350884",
        "stock_quantity": 10
    }
    form = BookForm(data=data)
    is_valid = await form.is_valid()
    assert is_valid is False
    assert "published_date" in form.get_errors()
    assert form.get_errors()["published_date"] == ["Published date cannot be in the future."]


@pytest.mark.asyncio
async def test_book_form_invalid_stock_quantity():
    # Invalid stock quantity (negative value)
    data = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "published_date": "2008-08-01",
        "isbn": "9780132350884",
        "stock_quantity": -5  # Negative value
    }
    form = BookForm(data=data)
    is_valid = await form.is_valid()
    assert is_valid is False
    assert "stock_quantity" in form.get_errors()
    assert form.get_errors()["stock_quantity"] == ["Stock quantity cannot be negative."]


@pytest.mark.asyncio
async def test_book_form_isbn_uniqueness():
    # Assuming the `is_isbn_unique` method returns False for a non-unique ISBN
    data = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "published_date": "2008-08-01",
        "isbn": "duplicate_isbn",  # Simulate a duplicate ISBN
        "stock_quantity": 10
    }

    class TestBookForm(BookForm):
        def is_isbn_unique(self, isbn):
            return False  # Simulating a duplicate ISBN

    form = TestBookForm(data=data)
    is_valid = await form.is_valid()
    assert is_valid is False
    assert "isbn" in form.get_errors()
    assert form.get_errors()["isbn"] == ["ISBN must be unique."]
