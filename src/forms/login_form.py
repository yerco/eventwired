from src.services.form_service import TextField, PasswordField, BaseForm, MinLengthValidator


class LoginForm(BaseForm):
    username = TextField(required=True, validators=[MinLengthValidator(3)])
    password = PasswordField(required=True, validators=[MinLengthValidator(3)])
