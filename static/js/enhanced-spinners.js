/**
 * Enhanced Loading Spinners
 * 
 * This script provides more visible loading indicators for various forms
 * and AJAX operations throughout the application.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize journal form spinner
    initJournalFormSpinner();
    
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
    const spinnerContainer = document.createElement('div');
    spinnerContainer.id = 'journal-spinner';
    spinnerContainer.className = 'journal-processing-spinner';
    spinnerContainer.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <div class="processing-message">
            Processing your journal entry... <br>
            <small class="text-muted">This may take a few seconds as your entry is being analyzed.</small>
        </div>
    `;
    
    // Add it after the form
    journalForm.parentNode.appendChild(spinnerContainer);
    
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
