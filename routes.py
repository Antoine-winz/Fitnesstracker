from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Workout, Exercise, Set
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/workout/new', methods=['GET', 'POST'])
def add_workout():
    if request.method == 'POST':
        workout_name = request.form.get('workout_name')
        notes = request.form.get('notes')
        
        workout = Workout(name=workout_name, notes=notes)
        db.session.add(workout)
        db.session.commit()
        
        return redirect(url_for('view_workout', workout_id=workout.id))
    return render_template('add_workout.html')

@app.route('/workout/<int:workout_id>')
def view_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    return render_template('view_workout.html', workout=workout)

@app.route('/workout/<int:workout_id>/exercise', methods=['POST'])
def add_exercise(workout_id):
    exercise_name = request.form.get('exercise_name')
    
    exercise = Exercise(name=exercise_name, workout_id=workout_id)
    db.session.add(exercise)
    db.session.commit()
    
    return jsonify({'exercise_id': exercise.id})

@app.route('/exercise/<int:exercise_id>/set', methods=['POST'])
def add_set(exercise_id):
    reps = request.form.get('reps')
    weight = request.form.get('weight')
    
    set = Set(exercise_id=exercise_id, reps=reps, weight=weight)
    db.session.add(set)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/workout/<int:workout_id>/delete', methods=['POST'])
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    db.session.delete(workout)
    db.session.commit()
    return redirect(url_for('history'))

@app.route('/workout/<int:workout_id>/duplicate', methods=['POST'])
def duplicate_workout(workout_id):
    original_workout = Workout.query.get_or_404(workout_id)
    new_workout = Workout(name=f"Copy of {original_workout.name}", notes=original_workout.notes)
    db.session.add(new_workout)
    
    for exercise in original_workout.exercises:
        new_exercise = Exercise(name=exercise.name, workout=new_workout)
        db.session.add(new_exercise)
        for set in exercise.sets:
            new_set = Set(reps=set.reps, weight=set.weight, exercise=new_exercise)
            db.session.add(new_set)
    
    db.session.commit()
    return redirect(url_for('view_workout', workout_id=new_workout.id))

@app.route('/history')
def history():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    return render_template('history.html', workouts=workouts)
