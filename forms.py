from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=64)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=64)])
    submit = SubmitField('Login')

class WorkoutForm(FlaskForm):
    name = StringField('Workout Name', validators=[DataRequired(), Length(min=3, max=32)])
    type = SelectField('Workout Type', choices=[('strength', 'Strength'), ('cardio', 'Cardio'), ('flexibility', 'Flexibility')], validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[('', 'Select'), ('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')], validators=[])
    description = StringField('Description', validators=[Length(max=256)])
    submit = SubmitField('Add Workout')

class ExerciseForm(FlaskForm):
    name = StringField('Exercise Name', validators=[DataRequired(), Length(min=3, max=32)])
    description = StringField('Description', validators=[Length(max=256)])
    video_url = StringField('Video URL', validators=[Length(max=256)])
    category = StringField('Category', validators=[Length(max=32)])
    equipment = StringField('Equipment', validators=[Length(max=64)])
    submit = SubmitField('Add Exercise')