/**
 * Enhanced Loading Spinners
 * 
 * This script provides more visible loading indicators for various forms
 * and AJAX operations throughout the application.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize journal form spinner
    initJournalFormSpinner();
    
    // Initialize all action buttons
    initAllActionButtons();
    
    // Create the global overlay spinner (hidden by default)
    createOverlaySpinner();
});

/**
 * Initialize the enhanced journal form spinner
 */
function initJournalFormSpinner() {
    const journalForm = document.getElementById('journal-form');
    
    if (!journalForm) return;
    
    // Create a visible spinner element that will be shown on submit
    const journalSpinnerContainer = document.createElement('div');
    journalSpinnerContainer.id = 'journal-spinner';
    journalSpinnerContainer.className = 'journal-processing-spinner';
    journalSpinnerContainer.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <div class="processing-message">
            Processing your journal entry... <br>
            <small class="text-muted">This may take a few seconds as your entry is being analyzed.</small>
        </div>
    `;
    
    // Add it after the form
    journalForm.parentNode.appendChild(journalSpinnerContainer);
    
    // Find the submit button
    const submitButton = document.getElementById('journal-submit-button');
    if (!submitButton) return;
    
    // Add form submission handler
    journalForm.addEventListener('submit', function(event) {
        // Check if form is valid before showing spinner
        if (journalForm.checkValidity()) {
            // Show both the button spinner and the more visible container spinner
            submitButton.innerHTML = '<div class="d-flex align-items-center justify-content-center"><span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...</div>';
            submitButton.disabled = true;
            
            // Show the more visible spinner
            document.getElementById('journal-spinner').style.display = 'block';
            
            // Log for debugging
            console.log('Journal spinner activated');
        }
    });
}

/**
 * Initialize all action buttons with enhanced spinners
 */
function initAllActionButtons() {
    // Find all buttons with type="submit" or button[type="button"] that don't have spinner-disabled class
    const actionButtons = document.querySelectorAll('button[type="submit"]:not(.spinner-disabled), button[type="button"]:not(.spinner-disabled)');
    
    actionButtons.forEach(button => {
        // Skip buttons that already have spinners via other methods
        if (button.id === 'journal-submit-button' || button.classList.contains('ajax-button')) {
            return;
        }
        
        // Create a data attribute to store original content
        button.setAttribute('data-original-content', button.innerHTML);
        
        // For all forms, add a submit handler
        if (button.type === 'submit') {
            const form = button.closest('form');
            if (form) {
                form.addEventListener('submit', function(event) {
                    if (form.checkValidity()) {
                        // Show spinner in button
                        button.innerHTML = '<div class="d-flex align-items-center justify-content-center"><span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...</div>';
                        button.disabled = true;
                    }
                });
            }
        } else {
            // For regular buttons, add click handler
            button.addEventListener('click', function() {
                // Only show spinner if button isn't disabled and doesn't have a data-no-spinner attribute
                if (!button.disabled && !button.hasAttribute('data-no-spinner')) {
                    const originalContent = button.innerHTML;
                    button.innerHTML = '<div class="d-flex align-items-center justify-content-center"><span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...</div>';
                    button.disabled = true;
                    
                    // Optional: If there's a data-spinner-timeout, reset after that time
                    const timeout = button.getAttribute('data-spinner-timeout');
                    if (timeout) {
                        setTimeout(() => {
                            button.innerHTML = originalContent;
                            button.disabled = false;
                        }, parseInt(timeout, 10));
                    }
                }
            });
        }
    });
}

/**
 * Creates a global overlay spinner
 */
function createOverlaySpinner() {
    // Create the overlay spinner element
    const overlaySpinner = document.createElement('div');
    overlaySpinner.id = 'global-loading-overlay';
    overlaySpinner.className = 'loading-overlay d-none';
    overlaySpinner.innerHTML = `
        <div class="spinner-border text-light" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <div class="loading-message">Processing your request...</div>
    `;
    
    // Add to body
    document.body.appendChild(overlaySpinner);
    
    // Add global functions
    window.showOverlaySpinner = function(message = 'Processing your request...') {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.querySelector('.loading-message').textContent = message;
            overlay.classList.remove('d-none');
        }
    };
    
    window.hideOverlaySpinner = function() {
        const overlay = document.getElementById('global-loading-overlay');
        if (overlay) {
            overlay.classList.add('d-none');
        }
    };
}

// Global functions to show/hide enhanced spinners
window.showEnhancedSpinner = function(buttonElement) {
    if (!buttonElement) return;
    
    // Store original content if not already stored
    if (!buttonElement.hasAttribute('data-original-content')) {
        buttonElement.setAttribute('data-original-content', buttonElement.innerHTML);
    }
    
    // Show spinner in button
    buttonElement.innerHTML = '<div class="d-flex align-items-center justify-content-center"><span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...</div>';
    buttonElement.disabled = true;
};

window.hideEnhancedSpinner = function(buttonElement) {
    if (!buttonElement) return;
    
    // Restore original content
    if (buttonElement.hasAttribute('data-original-content')) {
        buttonElement.innerHTML = buttonElement.getAttribute('data-original-content');
    } else {
        // Try to remove just the spinner if we don't have original content
        const spinner = buttonElement.querySelector('.spinner-border');
        if (spinner) {
            spinner.remove();
        }
    }
    
    buttonElement.disabled = false;
};
