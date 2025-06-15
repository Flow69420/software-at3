from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(8), default='user', nullable=False)
    profile_picture = db.Column(db.String(256), nullable=True, default='default.jpg')

    def __repr__(self):
        return f"<User {self.username}, {self.email}, {self.role}, {self.id}>"
    
class Workout(db.Model):
    __tablename__ = 'workouts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    type = db.Column(db.String(16), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(256), nullable=True)
    difficulty = db.Column(db.String(16), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('workouts', lazy=True))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    def __repr__(self):
        return f"<Workout {self.name}, User ID: {self.user_id}, Created At: {self.created_at}>"

class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(256), nullable=True)
    video_url = db.Column(db.String(256), nullable=True)
    category = db.Column(db.String(32), nullable=True)
    equipment = db.Column(db.String(64), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('exercises', lazy=True))

    def __repr__(self):
        return f"<Exercise {self.name}, User ID: {self.user_id}>"

class WorkoutExercise(db.Model):
    __tablename__ = 'workout_exercises'
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=3)
    reps = db.Column(db.Integer, nullable=False, default=10)
    rest_time = db.Column(db.Integer, nullable=True, default=60)
    weight = db.Column(db.Float, nullable=True, default=0.0)
    notes = db.Column(db.String(256), nullable=True)
    workout = db.relationship('Workout', backref=db.backref('workout_exercises', lazy=True))
    exercise = db.relationship('Exercise', backref=db.backref('workout_exercises', lazy=True))

    def __repr__(self):
        return f"<WorkoutExercise Workout ID: {self.workout_id}, Exercise ID: {self.exercise_id}, Order: {self.order}, Sets: {self.sets}, Reps: {self.reps}>"
