import pytest
from src.forms.login_form import LoginForm
from src.services.form_service import TextField, PasswordField


# Test that LoginForm initializes correctly and the fields are present
def test_login_form_initialization():
    form = LoginForm()

    # Assuming BaseForm stores fields in a dictionary or has a get_fields method
    assert 'username' in form.fields  # Adjust this to how BaseForm works
    assert 'password' in form.fields

    # Ensure the fields are instances of TextField and PasswordField respectively
    assert isinstance(form.fields['username'], TextField)  # Adjust this accordingly
    assert isinstance(form.fields['password'], PasswordField)


# Test that the form validates required fields successfully
@pytest.mark.asyncio
async def test_login_form_validation_success():
    # Simulating data submission with both username and password
    form = LoginForm(data={'username': 'testuser', 'password': 'securepassword'})

    # Ensure the form is valid when both required fields are provided
    assert await form.is_valid() is True

    # Check that there are no validation errors
    assert not form.errors


# Test that the form validation fails when required fields are missing
@pytest.mark.asyncio
async def test_login_form_validation_failure():
    # Case 1: Missing username
    form = LoginForm(data={'password': 'securepassword'})
    assert await form.is_valid() is False
    assert 'username' in form.errors

    # Case 2: Missing password
    form = LoginForm(data={'username': 'testuser'})
    assert await form.is_valid() is False
    assert 'password' in form.errors

    # Case 3: Missing both fields
    form = LoginForm(data={})
    assert await form.is_valid() is False
    assert 'username' in form.errors
    assert 'password' in form.errors
