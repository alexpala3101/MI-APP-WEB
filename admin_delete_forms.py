from flask_wtf import FlaskForm
from wtforms import HiddenField

class AdminDeleteUserForm(FlaskForm):
    csrf_token = HiddenField()
