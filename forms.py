from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_wtf.file import FileAllowed

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
    description = TextAreaField('Description', validators=[Length(max=256)])
    submit = SubmitField()

class ExerciseForm(FlaskForm):
    name = StringField('Exercise Name', validators=[DataRequired(), Length(min=3, max=32)])
    description = TextAreaField('Description', validators=[Length(max=256)])
    video_url = StringField('Video URL', validators=[Length(max=256)])
    category = StringField('Category', validators=[Length(max=32)])
    equipment = StringField('Equipment', validators=[Length(max=64)])
    submit = SubmitField()

class ProfileEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Update Profile')

class AddExerciseToWorkoutForm(FlaskForm):
    exercise = SelectField('Exercise', coerce=int, validators=[DataRequired()])
    sets = IntegerField('Sets', validators=[DataRequired()])
    reps = IntegerField('Reps', validators=[DataRequired()])
    order = IntegerField('Order', validators=[DataRequired()])
    rest_time = IntegerField('Rest Time (seconds)', validators=[])
    weight = IntegerField('Weight (kg)', validators=[])
    notes = TextAreaField('Notes', validators=[Length(max=256)])
    # Progression fields
    progression_interval = IntegerField('Progression Interval (completions)', validators=[])
    progression_weight_increment = IntegerField('Weight Increment (kg)', validators=[])
    progression_reps_increment = IntegerField('Reps Increment', validators=[])
    submit = SubmitField('Add to Workout')

class EditWorkoutExerciseForm(FlaskForm):
    sets = IntegerField('Sets', validators=[DataRequired()])
    reps = IntegerField('Reps', validators=[DataRequired()])
    order = IntegerField('Order', validators=[DataRequired()])
    rest_time = IntegerField('Rest Time (seconds)', validators=[])
    weight = IntegerField('Weight (kg)', validators=[])
    notes = TextAreaField('Notes', validators=[Length(max=256)])
    # Progression fields
    progression_interval = IntegerField('Progression Interval (completions)', validators=[])
    progression_weight_increment = IntegerField('Weight Increment (kg)', validators=[])
    progression_reps_increment = IntegerField('Reps Increment', validators=[])
    submit = SubmitField('Update')