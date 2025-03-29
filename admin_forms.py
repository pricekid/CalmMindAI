from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange

class AdminLoginForm(FlaskForm):
    """Form for admin login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class AdminMessageForm(FlaskForm):
    """Form for admin messages to users"""
    user_id = HiddenField('User ID', validators=[DataRequired()])
    journal_id = HiddenField('Journal ID', validators=[DataRequired()])
    message = TextAreaField('Message to User', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send Message')

class APIConfigForm(FlaskForm):
    """Form for updating OpenAI API configuration"""
    api_key = StringField('OpenAI API Key')
    max_tokens = IntegerField('Max Tokens', validators=[NumberRange(min=1, max=4000)], default=800)
    model = StringField('Model Name', validators=[DataRequired()], default="gpt-4o")
    submit = SubmitField('Update Configuration')