import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    import models
    import routes
    db.create_all()
    
    # Import and create necessary tables
    from models import CommonExercise
    if not CommonExercise.query.first():
        # Seed common exercises if none exist
        common_exercises = [
            {'name': 'Bench Press', 'category': 'Chest'},
            {'name': 'Squat', 'category': 'Legs'},
            {'name': 'Deadlift', 'category': 'Back'},
            {'name': 'Overhead Press', 'category': 'Shoulders'},
            {'name': 'Pull-ups', 'category': 'Back'},
            {'name': 'Push-ups', 'category': 'Chest'},
            {'name': 'Barbell Row', 'category': 'Back'},
            {'name': 'Leg Press', 'category': 'Legs'},
            {'name': 'Dumbbell Curl', 'category': 'Arms'},
            {'name': 'Tricep Extension', 'category': 'Arms'}
        ]
        for exercise in common_exercises:
            db.session.add(CommonExercise(**exercise))
        db.session.commit()
