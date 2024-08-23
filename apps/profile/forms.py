from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import DataRequired, EqualTo

class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('new_password', message='Passwords must match')
    ])