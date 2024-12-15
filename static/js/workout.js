document.addEventListener('DOMContentLoaded', function() {
    // Initialize toastr
    toastr.options = {
        "positionClass": "toast-top-right",
        "timeOut": "3000"
    };

    let currentExerciseId = null;

    // Exercise Modal Setup
    const exerciseModal = new bootstrap.Modal(document.getElementById('exerciseModal'));
    const setModal = new bootstrap.Modal(document.getElementById('setModal'));

    // Exercise name input with suggestions
    const exerciseNameInput = document.getElementById('exerciseName');
    if (exerciseNameInput) {
        let debounceTimeout;
        exerciseNameInput.addEventListener('input', function(e) {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(async () => {
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    try {
                        const response = await fetch(`/exercises/suggestions?q=${encodeURIComponent(query)}`);
                        const suggestions = await response.json();
                        
                        const datalist = document.getElementById('exerciseSuggestions');
                        datalist.innerHTML = '';
                        suggestions.forEach(suggestion => {
                            const option = document.createElement('option');
                            option.value = suggestion.name;
                            option.textContent = `${suggestion.name} (${suggestion.category || 'Uncategorized'})`;
                            datalist.appendChild(option);
                        });
                    } catch (error) {
                        console.error('Error fetching suggestions:', error);
                    }
                }
            }, 300); // Debounce delay
        });
    }
    
    // Add Exercise Button Handler
    const addExerciseBtn = document.getElementById('addExerciseBtn');
    if (addExerciseBtn) {
        addExerciseBtn.addEventListener('click', () => {
            document.getElementById('exerciseName').value = ''; // Clear the input
            exerciseModal.show();
        });
    }

    // Save Exercise Handler
    const saveExerciseBtn = document.getElementById('saveExercise');
    if (saveExerciseBtn) {
        saveExerciseBtn.addEventListener('click', async () => {
            const exerciseName = document.getElementById('exerciseName').value.trim();
            if (!exerciseName) {
                toastr.error('Please enter an exercise name');
                return;
            }

            const workoutId = window.location.pathname.split('/').pop();
            try {
                const response = await fetch(`/workout/${workoutId}/exercise`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        'exercise_name': exerciseName
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    toastr.success('Exercise added successfully');
                    exerciseModal.hide();
                    window.location.reload();
                } else {
                    toastr.error(data.error || 'Failed to add exercise');
                }
            } catch (error) {
                toastr.error('Error adding exercise');
                console.error('Error:', error);
            }
        });
    }

    // Add Set Button Handlers
    document.querySelectorAll('.add-set-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentExerciseId = btn.dataset.exerciseId;
            document.getElementById('reps').value = '';
            document.getElementById('weight').value = '';
            setModal.show();
        });
    });

    // Save Set Handler
    const saveSetBtn = document.getElementById('saveSet');
    if (saveSetBtn) {
        saveSetBtn.addEventListener('click', async () => {
            const reps = document.getElementById('reps');
            const weight = document.getElementById('weight');
            
            if (!reps.value || !weight.value) {
                toastr.error('Please fill in all fields');
                return;
            }
            
            if (reps.value < 1 || weight.value < 0) {
                toastr.error('Please enter valid values');
                return;
            }

            try {
                const response = await fetch(`/exercise/${currentExerciseId}/set`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        'reps': reps.value,
                        'weight': weight.value
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    toastr.success('Set added successfully');
                    setModal.hide();
                    window.location.reload();
                } else {
                    toastr.error(data.error || 'Failed to add set');
                }
            } catch (error) {
                toastr.error('Error adding set');
                console.error('Error:', error);
            }
        });
    }

    // Delete Exercise Handlers
    document.querySelectorAll('.delete-exercise').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (confirm('Are you sure you want to delete this exercise?')) {
                const exerciseId = btn.dataset.exerciseId;
                try {
                    const response = await fetch(`/exercise/${exerciseId}/delete`, {
                        method: 'POST',
                    });

                    if (response.ok) {
                        toastr.success('Exercise deleted successfully');
                        btn.closest('.card').remove();
                    } else {
                        toastr.error('Failed to delete exercise');
                    }
                } catch (error) {
                    toastr.error('Error deleting exercise');
                    console.error('Error:', error);
                }
            }
        });
    });

    // Duplicate Workout Handler
    document.querySelectorAll('.duplicate-workout').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const workoutId = this.dataset.workoutId;
            
            try {
                const response = await fetch(`/workout/${workoutId}/duplicate`, {
                    method: 'POST',
                });
                const data = await response.json();
                
                if (data.success) {
                    toastr.success('Workout duplicated successfully');
                    window.location.href = `/workout/${data.workout_id}`;
                } else {
                    toastr.error(data.error || 'Failed to duplicate workout');
                }
            } catch (error) {
                toastr.error('Error duplicating workout');
                console.error('Error:', error);
            }
        });
    });
});
