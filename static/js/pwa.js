// Progressive Web App initialization for Dear Teddy

// Check if service workers are supported
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
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
                <p class="card-text">A new version of Dear Teddy is available!</p>
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
                    <span>Install Dear Teddy on your device for better experience</span>
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

// Install the PWA - exposed globally so it can be called from other scripts
window.triggerInstall = function() {
    if (!deferredPrompt) {
        // If deferredPrompt isn't available and we're on the install page,
        // show the manual instructions modal from install-button.js
        if (typeof showInstallInstructions === 'function') {
            showInstallInstructions();
            return;
        }
        
        // Otherwise redirect to install page
        window.location.href = '/install';
        return;
    }
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            localStorage.setItem('pwaInstalled', 'true');
            
            // Show success message if we're not on the install page
            if (window.location.pathname !== '/install') {
                const successMessage = document.createElement('div');
                successMessage.className = 'alert alert-success alert-dismissible fade show position-fixed bottom-0 end-0 m-3';
                successMessage.style.zIndex = '1050';
                successMessage.innerHTML = `
                    <strong><i class="fas fa-check-circle me-2"></i>Successfully installed!</strong>
                    <p class="mb-0">Dear Teddy has been added to your device.</p>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                `;
                document.body.appendChild(successMessage);
                
                // Automatically dismiss after 5 seconds
                setTimeout(() => {
                    try {
                        const alert = new bootstrap.Alert(successMessage);
                        alert.close();
                    } catch (e) {
                        successMessage.remove();
                    }
                }, 5000);
            }
        } else {
            console.log('User dismissed the install prompt');
        }
        
        // Clear the deferred prompt variable
        deferredPrompt = null;
        dismissInstallPromotion();
    });
}

// Alias for backward compatibility
function installPWA() {
    window.triggerInstall();
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
    console.log('Dear Teddy was installed');
    localStorage.setItem('pwaInstalled', 'true');
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
        banner.remove();
    }
});