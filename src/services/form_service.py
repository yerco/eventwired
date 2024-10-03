# Custom exception for validation errors
class ValidationError(Exception):
    def __init__(self, message, field_name=None):
        super().__init__(message)
        self.field_name = field_name
        self.message = message


# Base validator class to provide a template for custom validators
class Validator:
    def __call__(self, field):
        raise NotImplementedError("Each validator must implement the __call__ method.")


# Validator for minimum length of a string
class MinLengthValidator(Validator):
    def __init__(self, min_length):
        self.min_length = min_length

    def __call__(self, field):
        if field.value and len(field.value) < self.min_length:
            return f"Value must be at least {self.min_length} characters."


# Validator for maximum length of a string
class MaxLengthValidator(Validator):
    def __init__(self, max_length):
        self.max_length = max_length

    def __call__(self, field):
        if field.value and len(field.value) > self.max_length:
            return f"Value must be no more than {self.max_length} characters."


# Validator for checking valid email format
class EmailValidator(Validator):
    def __call__(self, field):
        if field.value and "@" not in field.value:
            return "Enter a valid email address."


# Validator to check if a numeric field is within a range
class RangeValidator(Validator):
    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, field):
        if field.value is not None:
            try:
                value = float(field.value)
                if self.min_value is not None and value < self.min_value:
                    return f"Value must be at least {self.min_value}."
                if self.max_value is not None and value > self.max_value:
                    return f"Value must be no more than {self.max_value}."
            except ValueError:
                return "Enter a valid number."


class IntegerValidator(Validator):
    def __call__(self, field):
        if field.value is not None:
            try:
                int(field.value)
            except (ValueError, TypeError):
                return "Enter a valid integer."


class Field:
    def __init__(self, field_type="text", required=True, value=None, validators=None):
        self.type = field_type
        self.required = required
        self.value = value
        self.validators = validators or []

    def set_value(self, value):
        # Ensure value is always a string, even if a list is passed
        if isinstance(value, list):
            self.value = value[0] if value else None
        else:
            self.value = value

    async def validate(self):
        errors = []
        if self.required and not self.value:
            errors.append("This field is required.")
        for validator in self.validators:
            error = validator(self)
            if error:
                errors.append(error)
        return errors


class TextField(Field):
    def __init__(self, required=True, value=None, validators=None):
        super().__init__(field_type="text", required=required, value=value, validators=validators)


class EmailField(Field):
    def __init__(self, required=True, value=None, validators=None):
        default_validators = [EmailValidator()]
        super().__init__(field_type="email", required=required, value=value, validators=validators or default_validators)


class NumberField(Field):
    def __init__(self, required=True, value=None, validators=None):
        default_validators = [RangeValidator()] if validators is None else validators
        super().__init__(field_type="number", required=required, value=value, validators=default_validators)


class IntegerField(Field):
    def __init__(self, required=True, value=None, validators=None):
        default_validators = [IntegerValidator()]
        super().__init__(field_type="integer", required=required, value=value, validators=validators or default_validators)


class PasswordField(TextField):
    pass


class FormMeta(type):
    def __new__(cls, name, bases, attrs):
        fields = {key: value for key, value in attrs.items() if isinstance(value, Field)}
        for field_name in fields.keys():
            attrs.pop(field_name)  # Remove field definitions from class attributes
        attrs['_fields'] = fields  # Store fields in _fields
        return super().__new__(cls, name, bases, attrs)


class BaseForm(metaclass=FormMeta):
    def __init__(self, data=None):
        # Automatically clean form data to ensure no lists
        self.data = {key: (value[0] if isinstance(value, list) else value) for key, value in (data or {}).items()}
        self.errors = {}
        self.fields = {name: field for name, field in self._fields.items()}  # Clone fields

        # Set initial values for each field
        for field_name, field in self.fields.items():
            if field_name in self.data:
                field.set_value(self.data[field_name])

    async def is_valid(self):
        self.errors = {}
        is_valid = True
        for field_name, field in self.fields.items():
            field.set_value(self.data.get(field_name))  # Ensure set_value is used here
            field_errors = await field.validate()
            if field_errors:
                is_valid = False
                self.errors[field_name] = field_errors
        return is_valid

    def get_errors(self):
        return self.errors


class FormService:
    def __init__(self):
        pass

    async def create_form(self, form_class, data=None):
        return form_class(data=data)

    async def validate_form(self, form):
        is_valid = await form.is_valid()
        if is_valid:
            return True, None
        return False, form.get_errors()
