document.addEventListener('DOMContentLoaded', function() {
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

        if (response.ok) {
            location.reload();
        }
    });
});
