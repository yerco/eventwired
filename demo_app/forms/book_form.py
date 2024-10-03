from datetime import date

from src.services.form_service import BaseForm, TextField, IntegerField


class BookForm(BaseForm):
    title = TextField(required=True)
    author = TextField(required=True)
    published_date = TextField(required=False)
    isbn = TextField(required=False)
    stock_quantity = IntegerField(required=False)

    async def is_valid(self):
        is_valid = await super().is_valid()

        # Custom validation logic for `published_date`
        if self.data.get('published_date'):
            try:
                published_date = date.fromisoformat(self.data['published_date'])
                if published_date > date.today():
                    self.errors['published_date'] = ["Published date cannot be in the future."]
                    is_valid = False
            except ValueError:
                self.errors['published_date'] = ["Enter a valid date in YYYY-MM-DD format."]
                is_valid = False

        # Example: Custom validation logic for `isbn` uniqueness
        # (assuming we have a method `is_isbn_unique` to check uniqueness)
        if self.data.get('isbn'):
            isbn = self.data['isbn']
            if not self.is_isbn_unique(isbn):
                self.errors['isbn'] = ["ISBN must be unique."]
                is_valid = False

        # Business validation for `stock_quantity`
        if self.data.get('stock_quantity') is not None:
            if int(self.data['stock_quantity']) < 0:
                self.errors['stock_quantity'] = ["Stock quantity cannot be negative."]
                is_valid = False

        return is_valid


    def is_isbn_unique(self, isbn):
        # Placeholder logic for checking ISBN uniqueness, e.g., by querying a database
        return True  # Replace with actual uniqueness check
