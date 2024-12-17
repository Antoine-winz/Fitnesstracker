from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from models import Workout, Exercise, Set
from datetime import datetime

import re

def parse_exercise_list():
    exercises = []
    current_category = None
    with open('Pasted-Here-s-a-comprehensive-list-of-250-common-exercises-categorized-by-body-region-to-ensure-a-full-bo-1734470713381.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('####'):
                # Remove asterisks and clean up the category name
                current_category = line.replace('#', '').replace('*', '').strip()
            elif re.match(r'^\d+\.', line):
                exercise_name = re.sub(r'^\d+\.\s*', '', line.strip())
                if exercise_name:
                    exercises.append({
                        'name': exercise_name,
                        'category': current_category
                    })
    return exercises

EXERCISE_LIST = parse_exercise_list()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/workout/new', methods=['GET', 'POST'])
def add_workout():
    if request.method == 'POST':
        workout_name = request.form.get('workout_name')
        if workout_name:
            workout = Workout(name=workout_name, date=datetime.now())
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
    workout = Workout.query.get_or_404(workout_id)
    exercise_name = request.form.get('exercise_name')
    if exercise_name:
        exercise = Exercise(name=exercise_name, workout=workout)
        db.session.add(exercise)
        db.session.commit()
    return redirect(url_for('view_workout', workout_id=workout_id))

@app.route('/exercise/<int:exercise_id>/set', methods=['POST'])
def add_set(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    reps = request.form.get('reps', type=int)
    weight = request.form.get('weight', type=float)
    if reps is not None and weight is not None:
        set = Set(reps=reps, weight=weight, exercise=exercise)
        db.session.add(set)
        db.session.commit()
    return redirect(url_for('view_workout', workout_id=exercise.workout_id))

@app.route('/exercise/<int:exercise_id>/duplicate', methods=['POST'])
def duplicate_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    new_exercise = Exercise(
        name=exercise.name,
        workout_id=exercise.workout_id
    )
    db.session.add(new_exercise)
    for set in exercise.sets:
        new_set = Set(
            reps=set.reps,
            weight=set.weight,
            exercise=new_exercise
        )
        db.session.add(new_set)
    db.session.commit()
    return redirect(url_for('view_workout', workout_id=exercise.workout_id))

@app.route('/exercise/<int:exercise_id>/rename', methods=['POST'])
def rename_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    new_name = request.form.get('exercise_name')
    if new_name:
        exercise.name = new_name
        db.session.commit()
    return redirect(url_for('view_workout', workout_id=exercise.workout_id))

@app.route('/api/exercises/categories', methods=['GET'])
def get_categories():
    categories = sorted(list(set(exercise['category'] for exercise in EXERCISE_LIST)))
    return jsonify(categories)

@app.route('/api/exercises/suggest', methods=['GET'])
def suggest_exercises():
    query = request.args.get('q', '').lower()
    category = request.args.get('category', 'all')
    
    suggestions = []
    for exercise in EXERCISE_LIST:
        name_matches = query in exercise['name'].lower()
        category_matches = category == 'all' or category == exercise['category']
        
        if (name_matches or not query) and category_matches:
            exercise_with_category = {
                'name': exercise['name'],
                'category': exercise['category'],
                'display': f"{exercise['name']} ({exercise['category']})"
            }
            suggestions.append(exercise_with_category)
    
    return jsonify(suggestions[:20])

@app.route('/exercise/<int:exercise_id>/delete', methods=['POST'])
def delete_exercise(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    workout_id = exercise.workout_id
    db.session.delete(exercise)
    db.session.commit()
    return redirect(url_for('view_workout', workout_id=workout_id))

@app.route('/set/<int:set_id>/duplicate', methods=['POST'])
def duplicate_set(set_id):
    set = Set.query.get_or_404(set_id)
    new_set = Set(reps=set.reps, weight=set.weight, exercise_id=set.exercise_id)
    db.session.add(new_set)
    db.session.commit()
    return redirect(url_for('view_workout', workout_id=set.exercise.workout_id))

@app.route('/history')
def history():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    return render_template('history.html', workouts=workouts)

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

@app.route('/workout/<int:workout_id>/rename', methods=['POST'])
def rename_workout(workout_id):
    workout = Workout.query.get_or_404(workout_id)
    new_name = request.form.get('workout_name')
    if new_name:
        workout.name = new_name
        db.session.commit()
        return redirect(request.referrer or url_for('history'))
    return redirect(url_for('history'))