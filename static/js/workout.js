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

// Utility functions for notifications
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-toast`;
    notification.innerHTML = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }, 100);
}

// Loading spinner utility
function toggleLoading(element, isLoading) {
    if (isLoading) {
        const spinner = document.createElement('span');
        spinner.className = 'loading-spinner';
        element.prepend(spinner);
        element.disabled = true;
    } else {
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) spinner.remove();
        element.disabled = false;
    }
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
            toggleLoading(addExerciseBtn, true);
            try {
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
                    exerciseModal.show();
                } else {
                    showNotification('Failed to load categories', 'error');
                }
            } catch (error) {
                showNotification('An error occurred while loading categories', 'error');
            } finally {
                toggleLoading(addExerciseBtn, false);
            }
        });
    }

    // Exercise name autocomplete with debouncing
    const exerciseNameInput = document.getElementById('exerciseName');
    const exerciseList = document.getElementById('exerciseList');
    let debounceTimer;

    if (exerciseNameInput) {
        exerciseNameInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(async () => {
                const query = e.target.value;
                if (query.length >= 2 || currentCategory !== 'all') {
                    try {
                        const response = await fetch(`/api/exercises/suggest?q=${encodeURIComponent(query)}&category=${encodeURIComponent(currentCategory)}`);
                        if (response.ok) {
                            const suggestions = await response.json();
                            exerciseList.innerHTML = suggestions
                                .map(exercise => `<option value="${exercise.name}" label="${exercise.display}">`)
                                .join('');
                        }
                    } catch (error) {
                        showNotification('Failed to load suggestions', 'error');
                    }
                }
            }, 300); // Debounce delay
        });
    }

    // Save Exercise
    const saveExerciseBtn = document.getElementById('saveExercise');
    if (saveExerciseBtn) {
        saveExerciseBtn.addEventListener('click', async () => {
            const exerciseName = document.getElementById('exerciseName').value;
            if (!exerciseName.trim()) {
                showNotification('Please enter an exercise name', 'warning');
                return;
            }

            toggleLoading(saveExerciseBtn, true);
            try {
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
                    showNotification('Exercise added successfully');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showNotification('Failed to add exercise', 'error');
                }
            } catch (error) {
                showNotification('An error occurred while saving', 'error');
            } finally {
                toggleLoading(saveExerciseBtn, false);
            }
        });
    }

    // Add Set functionality
    document.querySelectorAll('.add-set-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            currentExerciseId = e.target.dataset.exerciseId;
            document.getElementById('reps').value = '';
            document.getElementById('weight').value = '';
            setModal.show();
        });
    });

    // Save Set
    const saveSetBtn = document.getElementById('saveSet');
    if (saveSetBtn) {
        saveSetBtn.addEventListener('click', async () => {
            const reps = document.getElementById('reps').value;
            const weight = document.getElementById('weight').value;

            if (!reps || !weight) {
                showNotification('Please fill in all fields', 'warning');
                return;
            }

            toggleLoading(saveSetBtn, true);
            try {
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
                    showNotification('Set added successfully');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showNotification('Failed to add set', 'error');
                }
            } catch (error) {
                showNotification('An error occurred while saving', 'error');
            } finally {
                toggleLoading(saveSetBtn, false);
            }
        });
    }

    // Add validation for number inputs
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', (e) => {
            if (e.target.value < 0) e.target.value = 0;
        });
    });
});
