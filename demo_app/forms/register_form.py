from src.services.form_service import BaseForm, TextField, PasswordField


class RegisterForm(BaseForm):
    username = TextField(required=True)
    password = PasswordField(required=True)
    confirm_password = PasswordField(required=True)

    async def is_valid(self):
        is_valid = await super().is_valid()

        # Custom validation for matching password and confirm_password
        if self.fields['password'].value != self.fields['confirm_password'].value:
            self.errors['confirm_password'] = ["Passwords do not match."]
            is_valid = False

        return is_valid
