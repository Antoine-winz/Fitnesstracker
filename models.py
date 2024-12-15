from datetime import datetime
from app import db

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    exercises = db.relationship('Exercise', backref='workout', lazy=True, cascade="all, delete-orphan")

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    sets = db.relationship('Set', backref='exercise', lazy=True, cascade="all, delete-orphan")

class Set(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)

class CommonExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50))  # e.g., 'Chest', 'Legs', 'Back'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    use_count = db.Column(db.Integer, default=0)  # Track how often this exercise is used
