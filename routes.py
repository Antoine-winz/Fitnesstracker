from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Workout, Exercise, Set, CommonExercise
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

@app.route('/exercises/suggestions', methods=['GET'])
def get_exercise_suggestions():
    query = request.args.get('q', '').strip().lower()
    suggestions = CommonExercise.query.filter(
        CommonExercise.name.ilike(f'%{query}%')
    ).order_by(CommonExercise.use_count.desc()).limit(5).all()
    
    return jsonify([{'id': ex.id, 'name': ex.name, 'category': ex.category} for ex in suggestions])

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
        
        # Update or create common exercise
        common_exercise = CommonExercise.query.filter_by(name=exercise_name).first()
        if common_exercise:
            common_exercise.use_count += 1
        else:
            common_exercise = CommonExercise(name=exercise_name)
            db.session.add(common_exercise)
        
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
@app.route('/admin/seed-exercises', methods=['POST'])
def seed_exercises():
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
    
    try:
        for exercise in common_exercises:
            if not CommonExercise.query.filter_by(name=exercise['name']).first():
                db.session.add(CommonExercise(**exercise))
        db.session.commit()
        return jsonify({'message': 'Successfully seeded common exercises'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500