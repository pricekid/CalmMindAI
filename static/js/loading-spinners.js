/**
 * Loading Spinners Utility
 * 
 * This script adds loading spinners to form buttons and AJAX requests.
 * It shows a spinner and loading message when a form is submitted or
 * when AJAX requests are made, and hides them when the operation completes.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all forms with loading spinners
    initFormLoadingSpinners();
    
    // Initialize AJAX buttons with loading spinners
    initAjaxLoadingSpinners();
});

/**
 * Initializes loading spinners for all forms
 */
function initFormLoadingSpinners() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Skip forms with the 'no-spinner' class
        if (form.classList.contains('no-spinner')) {
            return;
        }
        
        // Find submit button
        const submitButton = form.querySelector('button[type="submit"]');
        if (!submitButton) return;
        
        // Create loading spinner if it doesn't exist
        if (!form.querySelector('.loading-spinner-container')) {
            const loadingContainer = createLoadingSpinner();
            submitButton.insertAdjacentElement('afterend', loadingContainer);
        }
        
        // Add submit event listener
        form.addEventListener('submit', function() {
            // Only show spinner if form is valid
            if (form.checkValidity()) {
                const loadingSpinner = form.querySelector('.loading-spinner-container');
                if (loadingSpinner) {
                    submitButton.disabled = true;
                    loadingSpinner.classList.remove('d-none');
                }
            }
        });
    });
}

/**
 * Initializes loading spinners for AJAX buttons
 */
function initAjaxLoadingSpinners() {
    const ajaxButtons = document.querySelectorAll('.ajax-button');
    
    ajaxButtons.forEach(button => {
        // Create loading spinner if it doesn't exist
        if (!button.nextElementSibling || !button.nextElementSibling.classList.contains('loading-spinner-container')) {
            const loadingContainer = createLoadingSpinner();
            button.insertAdjacentElement('afterend', loadingContainer);
        }
        
        // Add click event listener
        button.addEventListener('click', function() {
            const loadingSpinner = button.nextElementSibling;
            if (loadingSpinner && loadingSpinner.classList.contains('loading-spinner-container')) {
                button.disabled = true;
                loadingSpinner.classList.remove('d-none');
                
                // The actual AJAX request will be handled by specific functionality
                // This just ensures the spinner is shown
            }
        });
    });
}

/**
 * Creates a loading spinner element
 * @returns {HTMLDivElement} The loading spinner container
 */
function createLoadingSpinner() {
    const container = document.createElement('div');
    container.className = 'loading-spinner-container d-none mt-3';
    
    container.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <span>Just a moment — we're processing your request.</span>
        </div>
    `;
    
    return container;
}

/**
 * Shows a loading spinner for a specific button
 * @param {HTMLElement} button - The button to show the spinner for
 * @param {boolean} disable - Whether to disable the button
 */
function showButtonSpinner(button, disable = true) {
    if (!button) return;
    
    // Find or create the spinner
    let spinner = button.nextElementSibling;
    if (!spinner || !spinner.classList.contains('loading-spinner-container')) {
        spinner = createLoadingSpinner();
        button.insertAdjacentElement('afterend', spinner);
    }
    
    // Show the spinner and optionally disable the button
    spinner.classList.remove('d-none');
    if (disable) {
        button.disabled = true;
    }
}

/**
 * Hides a loading spinner for a specific button
 * @param {HTMLElement} button - The button to hide the spinner for
 * @param {boolean} enable - Whether to enable the button
 */
function hideButtonSpinner(button, enable = true) {
    if (!button) return;
    
    // Find the spinner
    const spinner = button.nextElementSibling;
    if (spinner && spinner.classList.contains('loading-spinner-container')) {
        spinner.classList.add('d-none');
    }
    
    // Optionally enable the button
    if (enable) {
        button.disabled = false;
    }
}

// Add to window object for global access
window.showButtonSpinner = showButtonSpinner;
window.hideButtonSpinner = hideButtonSpinner;
