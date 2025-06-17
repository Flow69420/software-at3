from flask import Flask
from flask import render_template, redirect, url_for, flash, request

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db, User, Workout, Exercise

from flask_migrate import Migrate

db.init_app(app)

migrate = Migrate(app, db)

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from forms import RegistrationForm, LoginForm, WorkoutForm, ExerciseForm, ProfileEditForm

# with app.app_context():
#     db.create_all()

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username, email=current_user.email, active_section='home', profile_picture=current_user.profile_picture)

@app.route('/dashboard/workouts')
@login_required
def workouts():
    form = WorkoutForm()
    exercise_form = ExerciseForm()
    workout_type = request.args.get('type')
    query = Workout.query.filter_by(user_id=current_user.id)
    
    if workout_type:
        query = query.filter_by(type=workout_type)
    
    user_workouts = query.order_by(Workout.created_at.desc()).all()
    user_exercises = Exercise.query.filter_by(user_id=current_user.id).order_by(Exercise.id.desc()).all()
    return render_template(
        'dashboard.html',
        username=current_user.username,
        email=current_user.email,
        active_section='workouts',
        workout_form=form,
        exercise_form=exercise_form,
        workouts=user_workouts,
        exercises=user_exercises,
        selected_type=workout_type
    )

@app.route('/dashboard/workouts/create', methods=['POST'])
@login_required
def create_workout():
    form = WorkoutForm()
    if form.validate_on_submit():
        new_workout = Workout(
            name=form.name.data,
            type=form.type.data,
            duration=form.duration.data,
            difficulty=form.difficulty.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db.session.add(new_workout)
        db.session.commit()
        flash('Workout created!', 'success')
    else:
        flash('Error creating workout.', 'danger')
    return redirect(url_for('workouts'))

@app.route('/dashboard/exercises/create', methods=['POST'])
@login_required
def create_exercise():
    form = ExerciseForm()
    if form.validate_on_submit():
        new_exercise = Exercise(
            name=form.name.data,
            description=form.description.data,
            video_url=form.video_url.data,
            category=form.category.data,
            equipment=form.equipment.data,
            user_id=current_user.id
        )
        db.session.add(new_exercise)
        db.session.commit()
        flash('Exercise created!', 'success')
    else:
        flash('Error creating exercise.', 'danger')
    return redirect(url_for('workouts'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.profile_picture.data:
            filename = secure_filename(form.profile_picture.data.filename)
            picture_path = os.path.join('static', 'assets', filename)
            form.profile_picture.data.save(picture_path)
            current_user.profile_picture = filename
        from models import db
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    return render_template(
        'profile.html',
        username=current_user.username,
        email=current_user.email,
        profile_picture=current_user.profile_picture,
        form=form
    )