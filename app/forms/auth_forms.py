"""
app/forms/auth_forms.py

WTForms definitions for authentication.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """
    User login form.

    Fields:
        password: User's password.
        submit:   Form submission button.
    """
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Please enter your password.")]
    )
    submit = SubmitField("Log In")
