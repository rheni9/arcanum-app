"""
Authentication form for the Arcanum application.

Defines a WTForms-based login form for user password authentication,
with internationalization support.
"""

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l


class AuthForm(FlaskForm):
    """
    Represents the user login form.

    Provides fields for password input and form submission.
    """
    password = PasswordField(
        _l("Password"),
        validators=[DataRequired(message=_l("Please enter your password."))]
    )
    submit = SubmitField(_l("Sign In"))
