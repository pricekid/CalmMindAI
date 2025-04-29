// Progressive Web App initialization for Calm Journey

// Check if service workers are supported
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then((registration) => {
                console.log('Service Worker registered with scope:', registration.scope);
                
                // Check for updates to the Service Worker
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('Service Worker update found!');
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New content is available, show notification to user
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch((error) => {
                console.error('Service Worker registration failed:', error);
            });
            
        // Check for updates every hour
        setInterval(() => {
            navigator.serviceWorker.getRegistration().then((registration) => {
                if (registration) {
                    registration.update();
                }
            });
        }, 3600000); // 1 hour in milliseconds
    });
    
    // Listen for controlling service worker changing
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing) return;
        window.location.reload();
        refreshing = true;
    });
}

let refreshing = false;

// Function to show notification about app update
function showUpdateNotification() {
    const updateNotification = document.createElement('div');
    updateNotification.className = 'update-notification';
    updateNotification.innerHTML = `
        <div class="card bg-primary text-white position-fixed bottom-0 end-0 m-3" style="z-index: 9999; max-width: 300px;">
            <div class="card-header d-flex justify-content-between align-items-center">
                <span><i class="fas fa-sync-alt me-2"></i>Update Available</span>
                <button type="button" class="btn-close btn-close-white" aria-label="Close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="card-body">
                <p class="card-text">A new version of Calm Journey is available!</p>
                <button class="btn btn-sm btn-light" onclick="window.location.reload()">
                    <i class="fas fa-redo me-1"></i>Refresh Now
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(updateNotification);
}

// Handle "Add to Home Screen" functionality
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    // Store the event so it can be triggered later
    deferredPrompt = e;
    // Update UI to notify the user they can install the PWA
    showInstallPromotion();
});

// Show install promotion banner
function showInstallPromotion() {
    // Only show if not already installed and the install prompt is available
    if (!isAppInstalled() && deferredPrompt) {
        const installBanner = document.createElement('div');
        installBanner.id = 'pwa-install-banner';
        installBanner.className = 'position-fixed bottom-0 start-0 end-0 p-3 bg-dark text-white';
        installBanner.style.zIndex = '1050';
        installBanner.innerHTML = `
            <div class="container d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas fa-mobile-alt me-2"></i>
                    <span>Install Calm Journey on your device for better experience</span>
                </div>
                <div>
                    <button id="pwa-install-btn" class="btn btn-sm btn-primary me-2">Install</button>
                    <button id="pwa-dismiss-btn" class="btn btn-sm btn-outline-light">Not Now</button>
                </div>
            </div>
        `;
        document.body.appendChild(installBanner);
        
        // Add event listeners
        document.getElementById('pwa-install-btn').addEventListener('click', installPWA);
        document.getElementById('pwa-dismiss-btn').addEventListener('click', dismissInstallPromotion);
        
        // Save in local storage that we've shown the banner
        localStorage.setItem('pwaInstallPromptShown', Date.now());
    }
}

// Check if the app appears to be installed
function isAppInstalled() {
    // Check if it's in standalone mode or matches other installed PWA criteria
    if (window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true) {
        return true;
    }
    return false;
}

// Install the PWA
function installPWA() {
    if (!deferredPrompt) return;
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            localStorage.setItem('pwaInstalled', 'true');
        } else {
            console.log('User dismissed the install prompt');
        }
        
        // Clear the deferred prompt variable
        deferredPrompt = null;
        dismissInstallPromotion();
    });
}

// Dismiss the install promotion
function dismissInstallPromotion() {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.remove();
    }
    localStorage.setItem('pwaInstallPromptDismissed', Date.now());
}

// Handle "appinstalled" event
window.addEventListener('appinstalled', (evt) => {
    console.log('Calm Journey was installed');
    localStorage.setItem('pwaInstalled', 'true');
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.remove();
    }
});