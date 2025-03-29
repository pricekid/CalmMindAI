// Emoji Mood Selector JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Get all emoji options and the hidden input field
    const emojiOptions = document.querySelectorAll('.emoji-option');
    const moodScoreInput = document.getElementById('mood_score');
    const moodForm = document.getElementById('mood-form');
    
    // Add click event to each emoji option
    emojiOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Get the mood value from data attribute
            const moodValue = this.getAttribute('data-value');
            
            // Remove selected class from all options
            emojiOptions.forEach(opt => opt.classList.remove('selected'));
            
            // Add selected class to clicked option
            this.classList.add('selected');
            
            // Set the value in the hidden input
            moodScoreInput.value = moodValue;
            
            // Optional: Add a small animation or feedback
            animateSelection(this);
        });
    });
    
    // Form submission validation
    if (moodForm) {
        moodForm.addEventListener('submit', function(event) {
            if (!moodScoreInput.value) {
                event.preventDefault();
                
                // Shake the mood selector to indicate required selection
                const moodSelector = document.querySelector('.mood-selector');
                moodSelector.classList.add('shake');
                
                // Remove the shake class after animation completes
                setTimeout(() => {
                    moodSelector.classList.remove('shake');
                }, 500);
                
                // Show a message
                showMessage('Please select your mood first', 'warning');
            }
        });
    }
    
    // Function to animate selection
    function animateSelection(element) {
        // Add a small bounce effect
        element.style.transform = 'scale(1.3)';
        setTimeout(() => {
            element.style.transform = '';
        }, 150);
        
        // If there's tooltip message, show it briefly
        const tooltip = element.querySelector('.emoji-tooltip');
        if (tooltip) {
            tooltip.style.visibility = 'visible';
            tooltip.style.opacity = '1';
            
            setTimeout(() => {
                tooltip.style.visibility = '';
                tooltip.style.opacity = '';
            }, 1500);
        }
    }
    
    // Function to show feedback message
    function showMessage(message, type = 'info') {
        // Check if there's a feedback container
        let feedbackContainer = document.querySelector('.mood-feedback');
        
        if (!feedbackContainer) {
            // Create feedback container if it doesn't exist
            feedbackContainer = document.createElement('div');
            feedbackContainer.className = 'mood-feedback mt-2';
            const moodSelector = document.querySelector('.mood-selector');
            if (moodSelector) {
                moodSelector.parentNode.insertBefore(feedbackContainer, moodSelector.nextSibling);
            }
        }
        
        // Create alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to feedback container
        feedbackContainer.innerHTML = '';
        feedbackContainer.appendChild(alert);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                alert.remove();
            }, 150);
        }, 3000);
    }
    
    // Optional: Add hover effects or tooltips
    emojiOptions.forEach(option => {
        option.addEventListener('mouseenter', function() {
            // Play a subtle animation
            this.style.transform = 'scale(1.15)';
        });
        
        option.addEventListener('mouseleave', function() {
            // Reset the animation unless it's selected
            if (!this.classList.contains('selected')) {
                this.style.transform = '';
            }
        });
    });
    
    // Preselect a value if it exists in the form
    if (moodScoreInput && moodScoreInput.value) {
        const preselectedValue = moodScoreInput.value;
        const preselectedOption = document.querySelector(`.emoji-option[data-value="${preselectedValue}"]`);
        
        if (preselectedOption) {
            preselectedOption.classList.add('selected');
        }
    }
});