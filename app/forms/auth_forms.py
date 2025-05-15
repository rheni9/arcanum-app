"""
WTForms definitions for authentication.

Provides the login form for user authentication.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """
    User login form.

    Fields:
        password (PasswordField): User's password input.
        submit (SubmitField): Form submission button.
    """
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter your password.")
        ]
    )
    submit = SubmitField("Log In")
