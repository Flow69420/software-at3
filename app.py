from flask import Flask
from flask import render_template, redirect, url_for, flash, request, jsonify
from calendar import monthrange

app = Flask(__name__)
app.config.from_pyfile('config.py')

from models import db, User, Workout, Exercise, WorkoutExercise, WorkoutLog

from flask_migrate import Migrate

db.init_app(app)

migrate = Migrate(app, db)

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from forms import RegistrationForm, LoginForm, WorkoutForm, ExerciseForm, ProfileEditForm, AddExerciseToWorkoutForm, EditWorkoutExerciseForm

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
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch 3 most recent workouts
    recent_workouts = (
        Workout.query
        .filter_by(user_id=current_user.id)
        .order_by(Workout.created_at.desc())
        .limit(3)
        .all()
    )
    # Key stats
    total_workouts = Workout.query.filter_by(user_id=current_user.id).count()
    total_exercises = Exercise.query.filter_by(user_id=current_user.id).count()
    total_workouts_completed = WorkoutLog.query.filter_by(user_id=current_user.id).count()
    # Longest streak calculation
    completed_logs = WorkoutLog.query.filter_by(user_id=current_user.id).all()
    all_dates = sorted({log.date_completed for log in completed_logs})
    max_streak = 0
    current_streak = 0
    prev_date = None
    for d in all_dates:
        if prev_date and (d - prev_date).days == 1:
            current_streak += 1
        else:
            current_streak = 1
        max_streak = max(max_streak, current_streak)
        prev_date = d
    # Most recent workout completion
    most_recent_log = (
        WorkoutLog.query
        .filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.date_completed.desc())
        .first()
    )
    most_recent_workout = None
    most_recent_date = None
    if most_recent_log:
        most_recent_workout = Workout.query.get(most_recent_log.workout_id)
        most_recent_date = most_recent_log.date_completed
    # --- Chart Data for Preview ---
    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    activity_last_7 = {d: 0 for d in last_7_days}
    for log in completed_logs:
        if log.date_completed in activity_last_7:
            activity_last_7[log.date_completed] += 1
    activity_labels = [d.strftime('%a %d %b') for d in last_7_days]
    activity_data = [activity_last_7[d] for d in last_7_days]
    # Progression data
    progression_data = {}
    user_workouts = Workout.query.filter_by(user_id=current_user.id).all()
    user_workouts_serialized = [{'id': w.id, 'name': w.name} for w in user_workouts]
    for workout in user_workouts:
        workout_logs = (
            WorkoutLog.query
            .filter_by(user_id=current_user.id, workout_id=workout.id)
            .order_by(WorkoutLog.date_completed.asc())
            .all()
        )
        for we in WorkoutExercise.query.filter_by(workout_id=workout.id).all():
            weight = we.weight or 0
            reps = we.reps or 0
            interval = we.progression_interval or 0
            weight_inc = we.progression_weight_increment or 0
            reps_inc = we.progression_reps_increment or 0
            labels = []
            weights = []
            reps_list = []
            for idx, log in enumerate(workout_logs):
                labels.append(log.date_completed.strftime('%Y-%m-%d'))
                completed = idx + 1
                w = weight
                r = reps
                if interval and interval > 0:
                    w += (completed // interval) * weight_inc
                    r += (completed // interval) * reps_inc
                weights.append(w)
                reps_list.append(r)
            if workout.id not in progression_data:
                progression_data[workout.id] = {}
            progression_data[workout.id][we.exercise_id] = {
                'exercise_name': we.exercise.name,
                'labels': labels,
                'weights': weights,
                'reps': reps_list
            }
    return render_template(
        'dashboard.html',
        username=current_user.username,
        email=current_user.email,
        active_section='home',
        profile_picture=current_user.profile_picture,
        recent_workouts=recent_workouts,
        total_workouts=total_workouts,
        total_exercises=total_exercises,
        total_workouts_completed=total_workouts_completed,
        max_streak=max_streak,
        most_recent_workout=most_recent_workout,
        most_recent_date=most_recent_date,
        activity_labels=activity_labels,
        activity_data=activity_data,
        progression_data=progression_data,
        user_workouts=user_workouts_serialized
    )

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
        selected_type=workout_type,
        profile_picture=current_user.profile_picture
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

@app.route('/dashboard/workouts/<int:workout_id>/add_exercise', methods=['GET', 'POST'])
@login_required
def add_exercise_to_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)

    if workout.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('workouts'))
    form = AddExerciseToWorkoutForm()
    
    user_exercises = Exercise.query.filter_by(user_id=current_user.id).all()
    form.exercise.choices = [(e.id, e.name) for e in user_exercises]
    if form.validate_on_submit():
        new_we = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=form.exercise.data,
            sets=form.sets.data,
            reps=form.reps.data,
            order=form.order.data,
            rest_time=form.rest_time.data,
            weight=form.weight.data,
            notes=form.notes.data,
            progression_interval=form.progression_interval.data,
            progression_weight_increment=form.progression_weight_increment.data,
            progression_reps_increment=form.progression_reps_increment.data
        )
        db.session.add(new_we)
        db.session.commit()
        flash('Exercise added to workout!', 'success')
        return redirect(url_for('workouts'))
    return render_template('add_exercise_modal.html', form=form, workout=workout)

@app.route('/dashboard/workouts/<int:workout_id>/modal')
@login_required
def workout_detail_modal(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        return '', 403
    workout_exercises = (
        WorkoutExercise.query
        .filter_by(workout_id=workout_id)
        .order_by(WorkoutExercise.order.asc())
        .all()
    )
    return render_template('workout_detail_modal.html', workout=workout, workout_exercises=workout_exercises)

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

@app.route('/dashboard/workouts/<int:workout_id>/edit_exercise/<int:we_id>/modal', methods=['GET', 'POST'])
@login_required
def edit_workout_exercise_modal(workout_id, we_id):
    workout = Workout.query.get_or_404(workout_id)
    we = WorkoutExercise.query.get_or_404(we_id)
    if workout.user_id != current_user.id or we.workout_id != workout_id:
        return '', 403
    form = EditWorkoutExerciseForm(obj=we)
    if form.validate_on_submit():
        we.sets = form.sets.data
        we.reps = form.reps.data
        we.order = form.order.data
        we.rest_time = form.rest_time.data
        we.weight = form.weight.data
        we.notes = form.notes.data
        we.progression_interval = form.progression_interval.data
        we.progression_weight_increment = form.progression_weight_increment.data
        we.progression_reps_increment = form.progression_reps_increment.data
        db.session.commit()
        return '', 204
    return render_template('edit_workout_exercise_modal.html', form=form, we=we)

@app.route('/dashboard/workouts/<int:workout_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workout_modal(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        return '', 403
    form = WorkoutForm(obj=workout)
    if form.validate_on_submit():
        workout.name = form.name.data
        workout.type = form.type.data
        workout.duration = form.duration.data
        workout.difficulty = form.difficulty.data
        workout.description = form.description.data
        db.session.commit()
        return '', 204
    return render_template('edit_workout_modal.html', form=form, workout=workout)

@app.route('/dashboard/workouts/<int:workout_id>/add_exercise_drag', methods=['POST'])
@login_required
def add_exercise_drag(workout_id):
    data = request.get_json()
    exercise_id = data.get('exercise_id')
    
    if not exercise_id:
        return jsonify({'error': 'No exercise_id provided'}), 400
    workout = Workout.query.get_or_404(workout_id)
    exercise = Exercise.query.get_or_404(exercise_id)
    # Only allow the owner to add
    if workout.user_id != current_user.id or exercise.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    # Add with default values for sets/reps/order
    from models import WorkoutExercise
    order = len(workout.workout_exercises) + 1
    new_we = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=exercise_id,
        order=order,
        sets=3,
        reps=10
    )
    db.session.add(new_we)
    db.session.commit()
    return jsonify({'success': True}), 200

@app.route('/dashboard/exercises/<int:exercise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exercise_modal(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    if exercise.user_id != current_user.id:
        return '', 403
    form = ExerciseForm(obj=exercise)
    if form.validate_on_submit():
        exercise.name = form.name.data
        exercise.description = form.description.data
        exercise.video_url = form.video_url.data
        exercise.category = form.category.data
        exercise.equipment = form.equipment.data
        db.session.commit()
        return '', 204
    return render_template('edit_exercise_modal.html', form=form, exercise=exercise)

@app.route('/dashboard/tracking')
@login_required
def tracking():
    logs = (
        WorkoutLog.query
        .filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.date_completed.desc())
        .all()
    )
    # Group logs by date
    logs_by_date = defaultdict(list)
    for log in logs:
        logs_by_date[log.date_completed].append(log)
    # Sort dates descending
    sorted_dates = sorted(logs_by_date.keys(), reverse=True)
    # Fetch all workouts for the user
    user_workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.created_at.desc()).all()
    # For each workout, get all completion dates
    workout_completion_dates = {}
    for workout in user_workouts:
        dates = [log.date_completed.strftime('%Y-%m-%d') for log in WorkoutLog.query.filter_by(user_id=current_user.id, workout_id=workout.id).all()]
        workout_completion_dates[workout.id] = set(dates)
    today = date.today()
    year = today.year
    month = today.month
    first_weekday, days_in_month = monthrange(year, month)  # first_weekday: 0=Monday
    calendar_info = {
        'year': year,
        'month': month,
        'first_weekday': first_weekday,
        'days_in_month': days_in_month
    }
    return render_template(
        'dashboard.html',
        username=current_user.username,
        email=current_user.email,
        active_section='tracking',
        logs_by_date=logs_by_date,
        sorted_dates=sorted_dates,
        workouts=user_workouts,
        workout_completion_dates=workout_completion_dates,
        profile_picture=current_user.profile_picture,
        today=today,
        timedelta=timedelta,
        calendar_info=calendar_info
    )

@app.route('/dashboard/workouts/<int:workout_id>/complete', methods=['POST'])
@login_required
def complete_workout(workout_id):
    today = date.today()
    # Prevent duplicate log for same workout and date
    existing_log = WorkoutLog.query.filter_by(user_id=current_user.id, workout_id=workout_id, date_completed=today).first()
    if existing_log:
        flash('You have already completed this workout today!', 'info')
        return redirect(url_for('tracking'))
    new_log = WorkoutLog(user_id=current_user.id, workout_id=workout_id, date_completed=today)
    db.session.add(new_log)
    db.session.commit()

    # Progression logic
    from models import WorkoutExercise
    # Count completions for this workout
    completion_count = WorkoutLog.query.filter_by(user_id=current_user.id, workout_id=workout_id).count()
    workout_exercises = WorkoutExercise.query.filter_by(workout_id=workout_id).all()
    progression_msgs = []
    for we in workout_exercises:
        if we.progression_interval and we.progression_interval > 0:
            if completion_count % we.progression_interval == 0:
                if we.progression_weight_increment:
                    we.weight = (we.weight or 0) + we.progression_weight_increment
                    progression_msgs.append(f"{we.exercise.name}: +{we.progression_weight_increment}kg")
                if we.progression_reps_increment:
                    we.reps = (we.reps or 0) + we.progression_reps_increment
                    progression_msgs.append(f"{we.exercise.name}: +{we.progression_reps_increment} reps")
    db.session.commit()
    if progression_msgs:
        flash('Progression! ' + ' | '.join(progression_msgs), 'success')
    else:
        flash('Workout marked as completed!', 'success')
    return redirect(url_for('tracking'))

@app.route('/dashboard/stats')
@login_required
def stats():
    from models import WorkoutLog, Workout, Exercise, WorkoutExercise
    user_id = current_user.id
    # Total workouts completed
    total_workouts_completed = WorkoutLog.query.filter_by(user_id=user_id).count()
    # Total unique workouts
    total_unique_workouts = WorkoutLog.query.filter_by(user_id=user_id).distinct(WorkoutLog.workout_id).count()
    # Total exercises completed (sum of all exercises in completed workouts)
    completed_logs = WorkoutLog.query.filter_by(user_id=user_id).all()
    workout_ids = [log.workout_id for log in completed_logs]
    total_exercises_completed = WorkoutExercise.query.filter(WorkoutExercise.workout_id.in_(workout_ids)).count() if workout_ids else 0
    # Most performed workout
    from sqlalchemy import func
    most_performed = (
        db.session.query(WorkoutLog.workout_id, func.count(WorkoutLog.id).label('cnt'))
        .filter_by(user_id=user_id)
        .group_by(WorkoutLog.workout_id)
        .order_by(db.desc('cnt'))
        .first()
    )
    most_performed_workout = None
    most_performed_count = 0
    if most_performed:
        most_performed_workout = Workout.query.get(most_performed.workout_id)
        most_performed_count = most_performed.cnt
    # Streak: most consecutive days with a workout
    all_dates = sorted({log.date_completed for log in completed_logs})
    max_streak = 0
    current_streak = 0
    prev_date = None
    for d in all_dates:
        if prev_date and (d - prev_date).days == 1:
            current_streak += 1
        else:
            current_streak = 1
        max_streak = max(max_streak, current_streak)
        prev_date = d
    # Recent activity (last 7 days)
    from datetime import date, timedelta
    today = date.today()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]  # oldest to newest
    activity_last_7 = {d: 0 for d in last_7_days}
    for log in completed_logs:
        if log.date_completed in activity_last_7:
            activity_last_7[log.date_completed] += 1
    # Prepare labels and data for Chart.js
    activity_labels = [d.strftime('%a %d %b') for d in last_7_days]
    activity_data = [activity_last_7[d] for d in last_7_days]
    # --- Progression Data for Line Chart ---
    # For each workout, get all exercises and their progression over time
    # We'll build: {workout_id: {exercise_id: {labels: [dates], weights: [...], reps: [...]}}}
    progression_data = {}
    user_workouts = Workout.query.filter_by(user_id=user_id).all()
    # Serialize workouts for dropdowns (id and name only)
    user_workouts_serialized = [{'id': w.id, 'name': w.name} for w in user_workouts]
    for workout in user_workouts:
        workout_logs = (
            WorkoutLog.query
            .filter_by(user_id=user_id, workout_id=workout.id)
            .order_by(WorkoutLog.date_completed.asc())
            .all()
        )
        # For each exercise in this workout
        for we in WorkoutExercise.query.filter_by(workout_id=workout.id).all():
            # Start with initial values
            weight = we.weight or 0
            reps = we.reps or 0
            interval = we.progression_interval or 0
            weight_inc = we.progression_weight_increment or 0
            reps_inc = we.progression_reps_increment or 0
            # Build progression timeline
            labels = []
            weights = []
            reps_list = []
            for idx, log in enumerate(workout_logs):
                labels.append(log.date_completed.strftime('%Y-%m-%d'))
                # Calculate progression up to this log
                completed = idx + 1
                w = weight
                r = reps
                if interval and interval > 0:
                    w += (completed // interval) * weight_inc
                    r += (completed // interval) * reps_inc
                weights.append(w)
                reps_list.append(r)
            if workout.id not in progression_data:
                progression_data[workout.id] = {}
            progression_data[workout.id][we.exercise_id] = {
                'exercise_name': we.exercise.name,
                'labels': labels,
                'weights': weights,
                'reps': reps_list
            }
    return render_template(
        'stats.html',
        username=current_user.username,
        email=current_user.email,
        profile_picture=current_user.profile_picture,
        total_workouts_completed=total_workouts_completed,
        total_unique_workouts=total_unique_workouts,
        total_exercises_completed=total_exercises_completed,
        most_performed_workout=most_performed_workout,
        most_performed_count=most_performed_count,
        max_streak=max_streak,
        activity_labels=activity_labels,
        activity_data=activity_data,
        today=today,
        progression_data=progression_data,
        user_workouts=user_workouts_serialized,
        active_section='stats',
        selected_type=None
    )

@app.route('/dashboard/workouts/<int:workout_id>/delete', methods=['POST'])
@login_required
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    if workout.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('workouts'))
    # Delete related WorkoutExercise and WorkoutLog records
    WorkoutExercise.query.filter_by(workout_id=workout_id).delete()
    WorkoutLog.query.filter_by(workout_id=workout_id).delete()
    db.session.delete(workout)
    db.session.commit()
    flash('Workout deleted!', 'success')
    return redirect(url_for('workouts'))

@app.route('/dashboard/exercises/<int:exercise_id>/delete', methods=['POST'])
@login_required
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    if exercise.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('workouts'))
    # Delete related WorkoutExercise records
    WorkoutExercise.query.filter_by(exercise_id=exercise_id).delete()
    db.session.delete(exercise)
    db.session.commit()
    flash('Exercise deleted!', 'success')
    return redirect(url_for('workouts'))