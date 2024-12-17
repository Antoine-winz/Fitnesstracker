class WorkoutTimer {
    constructor() {
        this.minutes = 0;
        this.seconds = 0;
        this.totalSeconds = 0;
        this.interval = null;
        this.isRunning = false;
        this.sound = new Audio('/static/sounds/timer-end.mp3');

        // DOM elements
        this.minutesDisplay = document.getElementById('minutes');
        this.secondsDisplay = document.getElementById('seconds');
        this.startButton = document.getElementById('startTimer');
        this.pauseButton = document.getElementById('pauseTimer');
        this.resetButton = document.getElementById('resetTimer');
        this.minutesInput = document.getElementById('timerMinutes');
        this.secondsInput = document.getElementById('timerSeconds');

        // Event listeners
        this.startButton.addEventListener('click', () => this.start());
        this.pauseButton.addEventListener('click', () => this.pause());
        this.resetButton.addEventListener('click', () => this.reset());
        this.minutesInput.addEventListener('change', () => this.updateFromInput());
        this.secondsInput.addEventListener('change', () => this.updateFromInput());

        // Initialize display
        this.updateDisplay();
    }

    updateFromInput() {
        this.minutes = parseInt(this.minutesInput.value) || 0;
        this.seconds = parseInt(this.secondsInput.value) || 0;
        this.totalSeconds = this.minutes * 60 + this.seconds;
        this.updateDisplay();
    }

    updateDisplay() {
        const mins = Math.floor(this.totalSeconds / 60);
        const secs = this.totalSeconds % 60;
        this.minutesDisplay.textContent = mins.toString().padStart(2, '0');
        this.secondsDisplay.textContent = secs.toString().padStart(2, '0');
    }

    start() {
        if (!this.isRunning && this.totalSeconds > 0) {
            this.isRunning = true;
            this.interval = setInterval(() => {
                if (this.totalSeconds > 0) {
                    this.totalSeconds--;
                    this.updateDisplay();
                } else {
                    this.complete();
                }
            }, 1000);
            this.startButton.disabled = true;
            this.minutesInput.disabled = true;
            this.secondsInput.disabled = true;
        }
    }

    pause() {
        if (this.isRunning) {
            clearInterval(this.interval);
            this.isRunning = false;
            this.startButton.disabled = false;
        }
    }

    reset() {
        this.pause();
        this.updateFromInput();
        this.startButton.disabled = false;
        this.minutesInput.disabled = false;
        this.secondsInput.disabled = false;
    }

    complete() {
        this.pause();
        this.sound.play().catch(error => console.log('Error playing sound:', error));
        alert('Timer Complete!');
        this.reset();
    }
}

// Initialize timer when document is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('timerCard')) {
        window.workoutTimer = new WorkoutTimer();
    }
});
