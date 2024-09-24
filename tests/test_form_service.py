import pytest
from src.services.form_service import (
    FormService, TextField, EmailField, NumberField, PasswordField, BaseForm, MinLengthValidator, MaxLengthValidator, RangeValidator
)


# A sample form to test validation
class SampleForm(BaseForm):
    name = TextField(required=True, validators=[MinLengthValidator(3)])
    email = EmailField(required=True)
    age = NumberField(required=True, validators=[RangeValidator(min_value=18, max_value=99)])
    password = PasswordField(required=True, validators=[MinLengthValidator(6)])


@pytest.mark.asyncio
async def test_form_with_valid_data():
    form_service = FormService()
    data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30,
        'password': 'secret'
    }

    form = await form_service.create_form(SampleForm, data)
    is_valid, errors = await form_service.validate_form(form)

    assert is_valid is True, "Form should be valid with correct data."
    assert errors is None, "No errors should be returned for valid data."


@pytest.mark.asyncio
async def test_form_with_min_length_error():
    form_service = FormService()
    data = {
        'name': 'Jo',  # Too short
        'email': 'john@example.com',
        'age': 30,
        'password': 'secret'
    }

    form = await form_service.create_form(SampleForm, data)
    is_valid, errors = await form_service.validate_form(form)

    assert is_valid is False, "Form should be invalid due to short name."
    assert 'name' in errors, "The 'name' field should return an error for failing the min length validator."
    assert errors['name'] == ["Value must be at least 3 characters."]


@pytest.mark.asyncio
async def test_form_with_invalid_email():
    form_service = FormService()
    data = {
        'name': 'John Doe',
        'email': 'invalid-email',
        'age': 30,
        'password': 'secret'
    }

    form = await form_service.create_form(SampleForm, data)
    is_valid, errors = await form_service.validate_form(form)

    assert is_valid is False, "Form should be invalid with incorrect email format."
    assert 'email' in errors, "The 'email' field should return an error for invalid format."
    assert errors['email'] == ["Enter a valid email address."]


@pytest.mark.asyncio
async def test_form_with_number_range_error():
    form_service = FormService()
    data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 120,  # Out of range
        'password': 'secret'
    }

    form = await form_service.create_form(SampleForm, data)
    is_valid, errors = await form_service.validate_form(form)

    assert is_valid is False, "Form should be invalid due to age being out of range."
    assert 'age' in errors, "The 'age' field should return an error for being out of range."
    assert errors['age'] == ["Value must be no more than 99."]
