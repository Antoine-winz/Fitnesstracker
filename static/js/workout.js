function renameExercise(exerciseId, currentName) {
    const modal = new bootstrap.Modal(document.getElementById('exerciseRenameModal'));
    const form = document.getElementById('exerciseRenameForm');
    const input = document.getElementById('newExerciseName');
    
    input.value = currentName;
    form.action = `/exercise/${exerciseId}/rename`;
    modal.show();
}

function renameWorkout(workoutId, currentName) {
    const modal = new bootstrap.Modal(document.getElementById('renameModal'));
    const form = document.getElementById('renameForm');
    const input = document.getElementById('newWorkoutName');
    
    input.value = currentName;
    form.action = `/workout/${workoutId}/rename`;
    modal.show();
}

document.addEventListener('DOMContentLoaded', function() {
    // Add Exercise functionality
    const addExerciseBtn = document.getElementById('addExerciseBtn');
    const exerciseModal = new bootstrap.Modal(document.getElementById('exerciseModal'));
    const setModal = new bootstrap.Modal(document.getElementById('setModal'));
    let currentExerciseId = null;
    let currentCategory = 'all';

    if (addExerciseBtn) {
        addExerciseBtn.addEventListener('click', async () => {
            // Fetch categories and populate filters when modal is opened
            const response = await fetch('/api/exercises/categories');
            if (response.ok) {
                const categories = await response.json();
                const filterContainer = document.getElementById('categoryFilters');
                filterContainer.innerHTML = `
                    <button type="button" class="btn btn-outline-primary btn-sm active" data-category="all">All</button>
                    ${categories.map(category => 
                        `<button type="button" class="btn btn-outline-primary btn-sm" data-category="${category}">${category}</button>`
                    ).join('')}
                `;
                
                // Add click handlers to filter buttons
                filterContainer.querySelectorAll('button').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        filterContainer.querySelectorAll('button').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        currentCategory = btn.dataset.category;
                        // Trigger search with current input value
                        const event = new Event('input');
                        exerciseNameInput.dispatchEvent(event);
                    });
                });
            }
            exerciseModal.show();
        });
    }

    // Exercise name autocomplete
    const exerciseNameInput = document.getElementById('exerciseName');
    const exerciseList = document.getElementById('exerciseList');

    if (exerciseNameInput) {
        exerciseNameInput.addEventListener('input', async (e) => {
            const query = e.target.value;
            if (query.length >= 2 || currentCategory !== 'all') {
                const response = await fetch(`/api/exercises/suggest?q=${encodeURIComponent(query)}&category=${encodeURIComponent(currentCategory)}`);
                if (response.ok) {
                    const suggestions = await response.json();
                    exerciseList.innerHTML = suggestions
                        .map(exercise => `<option value="${exercise.name}" label="${exercise.display}">`)
                        .join('');
                }
            }
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
