from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, DateField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class UserLoginForm(FlaskForm):
    username = StringField('Usuario o Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class UserRegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=25)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Nombre Completo', validators=[DataRequired(), Length(min=3, max=50)])
    phone = StringField('Teléfono', validators=[Optional(), Length(min=7, max=20)])
    birthdate = DateField('Fecha de Nacimiento', validators=[Optional()], format='%Y-%m-%d')
    gender = SelectField('Género', choices=[('', 'Selecciona'), ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], validators=[Optional()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class UserEditProfileForm(FlaskForm):
    full_name = StringField('Nombre Completo', validators=[DataRequired(), Length(min=3, max=50)])
    phone = StringField('Teléfono', validators=[Optional(), Length(min=7, max=20)])
    birthdate = DateField('Fecha de Nacimiento', validators=[Optional()], format='%Y-%m-%d')
    gender = SelectField('Género', choices=[('', 'Selecciona'), ('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], validators=[Optional()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Guardar Cambios')

class UserChangePasswordForm(FlaskForm):
    current_password = PasswordField('Contraseña Actual', validators=[DataRequired()])
    new_password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Cambiar Contraseña')
