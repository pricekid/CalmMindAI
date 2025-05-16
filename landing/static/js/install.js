// A simple and robust approach for PWA installation
let installPrompt;

// Simple handler function for install clicks
function showInstallPrompt() {
    if (!installPrompt) {
        alert("Installation isn't available right now. This could be because:\n\n" +
              "• You've already installed the app\n" +
              "• Your browser doesn't support installation\n" +
              "• The app doesn't meet installation criteria yet\n\n" +
              "Try using Chrome or Edge for the best experience.");
        return;
    }
    
    // Show the installation prompt
    installPrompt.prompt();
    
    // Log the outcome
    installPrompt.userChoice.then(function(choiceResult) {
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            installPrompt = null;
        } else {
            console.log('User dismissed the install prompt');
        }
    });
}

// Listen for the browser's install prompt event
window.addEventListener('beforeinstallprompt', function(e) {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    
    // Save the event so it can be triggered later
    installPrompt = e;
    console.log('Install prompt ready');
});

// Track when the PWA is successfully installed
window.addEventListener('appinstalled', function(e) {
    console.log('Application was successfully installed');
    installPrompt = null;
});