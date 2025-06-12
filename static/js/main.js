/**
 * Main JavaScript file for Dear Teddy application
 */

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApplication();
});

function initializeApplication() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Initialize form validations
    initializeFormValidation();
    
    // Initialize PWA features
    initializePWA();
    
    console.log('Dear Teddy application initialized');
}

function initializeFormValidation() {
    // Add form validation for all forms
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

function initializePWA() {
    // Register service worker if available
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(function(registration) {
                console.log('Service Worker registered successfully');
            })
            .catch(function(error) {
                console.log('Service Worker registration failed');
            });
    }
    
    // Handle PWA install prompt
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', function(e) {
        e.preventDefault();
        deferredPrompt = e;
        showInstallPrompt();
    });
}

function showInstallPrompt() {
    // Show install button or banner
    const installBanner = document.getElementById('install-banner');
    if (installBanner) {
        installBanner.style.display = 'block';
    }
}

// Export functions for global use
window.DearTeddy = {
    initialize: initializeApplication,
    validateForm: initializeFormValidation,
    initPWA: initializePWA
};