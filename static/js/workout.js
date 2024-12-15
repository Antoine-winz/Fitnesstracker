document.addEventListener('DOMContentLoaded', function() {
    // Initialize toastr
    toastr.options = {
        "positionClass": "toast-top-right",
        "timeOut": "3000"
    };

    // Add Exercise functionality
    const addExerciseBtn = document.getElementById('addExerciseBtn');
    const exerciseModal = new bootstrap.Modal(document.getElementById('exerciseModal'));
    const setModal = new bootstrap.Modal(document.getElementById('setModal'));
    let currentExerciseId = null;

    if (addExerciseBtn) {
        addExerciseBtn.addEventListener('click', () => {
            exerciseModal.show();
        });
    }

    // Save Exercise
    document.getElementById('saveExercise')?.addEventListener('click', async () => {
        const exerciseName = document.getElementById('exerciseName').value;
        const workoutId = window.location.pathname.split('/').pop();

        const response = await fetch(`/workout/${workoutId}/exercise`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'workout_id': workoutId,
                'exercise_name': exerciseName
            })
        });

        if (response.ok) {
            location.reload();
        }
    });

    // Add Set functionality
    document.querySelectorAll('.add-set-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentExerciseId = e.target.dataset.exerciseId;
            setModal.show();
        });
    });

    // Save Set
    document.getElementById('saveSet')?.addEventListener('click', async () => {
        const reps = document.getElementById('reps').value;
        const weight = document.getElementById('weight').value;

        const response = await fetch(`/exercise/${currentExerciseId}/set`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'exercise_id': currentExerciseId,
                'reps': reps,
                'weight': weight
            })
        });

    // Delete Exercise functionality
    document.querySelectorAll('.delete-exercise').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if (confirm('Are you sure you want to delete this exercise?')) {
                const exerciseId = e.target.dataset.exerciseId;
                const response = await fetch(`/exercise/${exerciseId}/delete`, {
                    method: 'POST',
                });

                if (response.ok) {
                    toastr.success('Exercise deleted successfully');
                    e.target.closest('.card').remove();
                } else {
                    toastr.error('Failed to delete exercise');
                }
            }
        });
    });

    // Form validation for set input
    document.getElementById('saveSet')?.addEventListener('click', async () => {
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

        const response = await fetch(`/exercise/${currentExerciseId}/set`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'exercise_id': currentExerciseId,
                'reps': reps.value,
                'weight': weight.value
            })
        });

        if (response.ok) {
            toastr.success('Set added successfully');
            location.reload();
        } else {
            toastr.error('Failed to add set');
        }
    });

        if (response.ok) {
            location.reload();
        }
    });
});
