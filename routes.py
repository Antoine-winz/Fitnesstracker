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
    if not request.form:
        return jsonify({'error': 'No form data received'}), 400
        
    exercise_name = request.form.get('exercise_name', '').strip()
    if not exercise_name:
        return jsonify({'error': 'Exercise name is required'}), 400
        
    try:
        workout = Workout.query.get_or_404(workout_id)
        exercise = Exercise(name=exercise_name, workout_id=workout.id)
        db.session.add(exercise)
        db.session.commit()
        
        app.logger.info(f'Added exercise {exercise_name} to workout {workout_id}')
        return jsonify({
            'success': True,
            'exercise_id': exercise.id,
            'exercise_name': exercise.name
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error adding exercise: {str(e)}')
        return jsonify({'error': 'Failed to add exercise'}), 500

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