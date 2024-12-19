from datetime import datetime
from flask_login import UserMixin
from app import db
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

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
    
    @property
    def total_volume(self):
        """Calculate total volume (weight * reps) for all sets"""
        return sum(set.weight * set.reps for set in self.sets)
    
    @property
    def max_weight(self):
        """Get the maximum weight used across all sets"""
        if not self.sets:
            return 0
        return max(set.weight for set in self.sets)

class Set(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def volume(self):
        """Calculate volume (weight * reps) for this set"""
        return self.weight * self.reps
