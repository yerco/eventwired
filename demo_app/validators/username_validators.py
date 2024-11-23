import re

from demo_app.models.user import User
from src.services.form_service import Validator


class UsernameValidator(Validator):
    def __call__(self, field):
        value = field.value
        errors = []

        if not value:
            errors.append("Username cannot be empty.")
            return errors  # Early return since other checks depend on value

        if any(char.isspace() for char in value):
            errors.append("Username cannot contain whitespace.")
        if not re.match(r'^[A-Za-z0-9_]+$', value):
            errors.append("Username can only contain letters, numbers, and underscores.")
        if not (3 <= len(value) <= 30):
            errors.append("Username must be between 3 and 30 characters long.")

        return errors if errors else None
