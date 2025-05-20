// A simple and robust approach for PWA installation
let installPrompt;

// Handler function for install clicks
function showInstallPrompt() {
    if (!installPrompt) {
        // Instead of just showing an alert, redirect to the installation instructions page
        const goToInstructions = confirm(
            "Would you like to see detailed installation instructions for your device?\n\n" +
            "This will help you install Dear Teddy as an app on your phone, tablet, or computer."
        );
        
        if (goToInstructions) {
            // Redirect to the main app's install page
            window.location.href = "https://dearteddy-4vqj.onrender.com/install";
        }
        return;
    }
    
    // Show the installation prompt if available
    installPrompt.prompt();
    
    // Log the outcome
    installPrompt.userChoice.then(function(choiceResult) {
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            installPrompt = null;
            
            // Show success message
            setTimeout(function() {
                alert("Dear Teddy has been successfully installed!\n\nYou can now find it on your home screen or app drawer.");
            }, 1000);
        } else {
            console.log('User dismissed the install prompt');
            
            // Ask if they want instructions instead
            setTimeout(function() {
                const needHelp = confirm(
                    "Would you like to see detailed instructions for installing Dear Teddy manually?"
                );
                
                if (needHelp) {
                    window.location.href = "https://dearteddy-4vqj.onrender.com/install";
                }
            }, 500);
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