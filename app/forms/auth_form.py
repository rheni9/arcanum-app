"""
Authentication form for the Arcanum application.

Defines a WTForms-based login form for user password authentication.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """
    Represents the user login form.

    Provides fields for password input and form submission.
    """
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Please enter your password.")]
    )
    submit = SubmitField("Log In")
