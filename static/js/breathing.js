document.addEventListener('DOMContentLoaded', function() {
    const circleElement = document.getElementById('breathing-circle');
    const breathingText = document.getElementById('breathing-text');
    const startButton = document.getElementById('start-breathing');
    const stopButton = document.getElementById('stop-breathing');
    const durationSelect = document.getElementById('breathing-duration');
    
    let isBreathingActive = false;
    let breathingInterval;
    let currentPhase = 'inhale';
    let timer;
    let totalDuration = 120; // Default duration in seconds
    let timeRemaining = totalDuration;
    
    // Initialize timer display
    updateTimerDisplay();
    
    // Set up the animation phases
    const breathingPhases = {
        inhale: {
            duration: 4000, // 4 seconds
            nextPhase: 'hold1',
            text: 'Breathe in...',
            animation: 'scale(1.5)'
        },
        hold1: {
            duration: 4000, // 4 seconds
            nextPhase: 'exhale',
            text: 'Hold...',
            animation: 'scale(1.5)'
        },
        exhale: {
            duration: 6000, // 6 seconds
            nextPhase: 'hold2',
            text: 'Breathe out...',
            animation: 'scale(1)'
        },
        hold2: {
            duration: 2000, // 2 seconds
            nextPhase: 'inhale',
            text: 'Hold...',
            animation: 'scale(1)'
        }
    };
    
    // Update timer display
    function updateTimerDisplay() {
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        document.getElementById('timer-display').textContent = 
            `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
    
    // Start the breathing exercise
    startButton.addEventListener('click', function() {
        if (isBreathingActive) return;
        
        // Get selected duration
        totalDuration = parseInt(durationSelect.value);
        timeRemaining = totalDuration;
        updateTimerDisplay();
        
        isBreathingActive = true;
        startButton.disabled = true;
        stopButton.disabled = false;
        durationSelect.disabled = true;
        
        // Start countdown
        timer = setInterval(function() {
            timeRemaining--;
            updateTimerDisplay();
            
            if (timeRemaining <= 0) {
                stopBreathingExercise();
            }
        }, 1000);
        
        // Start with inhale phase
        changeBreathingPhase('inhale');
    });
    
    // Stop the breathing exercise
    stopButton.addEventListener('click', stopBreathingExercise);
    
    function stopBreathingExercise() {
        if (!isBreathingActive) return;
        
        clearInterval(breathingInterval);
        clearInterval(timer);
        
        isBreathingActive = false;
        startButton.disabled = false;
        stopButton.disabled = true;
        durationSelect.disabled = false;
        
        // Reset the circle
        circleElement.style.transform = 'scale(1)';
        breathingText.textContent = 'Click Start to begin';
        currentPhase = 'inhale';
        timeRemaining = totalDuration;
        updateTimerDisplay();
    }
    
    function changeBreathingPhase(phase) {
        if (!isBreathingActive) return;
        
        currentPhase = phase;
        const phaseInfo = breathingPhases[phase];
        
        // Update UI
        breathingText.textContent = phaseInfo.text;
        circleElement.style.transform = phaseInfo.animation;
        
        // Schedule next phase
        clearInterval(breathingInterval);
        breathingInterval = setTimeout(function() {
            changeBreathingPhase(phaseInfo.nextPhase);
        }, phaseInfo.duration);
    }
});
