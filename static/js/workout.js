document.addEventListener('DOMContentLoaded', function() {
    // Initialize toastr
    toastr.options = {
        "positionClass": "toast-top-right",
        "timeOut": "3000"
    };

    let currentExerciseId = null;

    // Add Exercise functionality
    const addExerciseBtn = document.getElementById('addExerciseBtn');
    if (addExerciseBtn) {
        const exerciseModal = new bootstrap.Modal(document.getElementById('exerciseModal'));
        
        addExerciseBtn.addEventListener('click', () => {
            exerciseModal.show();
        });

        document.getElementById('saveExercise').addEventListener('click', async () => {
            const exerciseName = document.getElementById('exerciseName').value;
            if (!exerciseName) {
                toastr.error('Please enter an exercise name');
                return;
            }

            const workoutId = window.location.pathname.split('/').pop();
            const response = await fetch(`/workout/${workoutId}/exercise`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'exercise_name': exerciseName
                })
            });

            if (response.ok) {
                toastr.success('Exercise added successfully');
                location.reload();
            } else {
                toastr.error('Failed to add exercise');
            }
            exerciseModal.hide();
        });
    }

    // Add Set functionality
    const addSetBtns = document.querySelectorAll('.add-set-btn');
    if (addSetBtns.length > 0) {
        const setModal = new bootstrap.Modal(document.getElementById('setModal'));
        
        addSetBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                currentExerciseId = btn.dataset.exerciseId;
                setModal.show();
            });
        });

        document.getElementById('saveSet').addEventListener('click', async () => {
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
                setModal.hide();
            } else {
                toastr.error('Failed to add set');
            }
        });
    }

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
});
