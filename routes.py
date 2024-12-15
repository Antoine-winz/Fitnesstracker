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

@app.route('/history')
def history():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    return render_template('history.html', workouts=workouts)

@app.route('/workout/<int:workout_id>/delete', methods=['POST'])
def delete_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    db.session.delete(workout)
    db.session.commit()
    flash('Workout deleted successfully', 'success')
    return redirect(url_for('history'))

@app.route('/exercise/<int:exercise_id>/delete', methods=['POST'])
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    workout_id = exercise.workout_id
    db.session.delete(exercise)
    db.session.commit()
    return jsonify({'success': True})