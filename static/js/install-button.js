// Install button functionality for Dear Teddy PWA

document.addEventListener('DOMContentLoaded', () => {
    // Create install button elements
    const createInstallButton = () => {
        const installContainer = document.createElement('div');
        installContainer.id = 'install-container';
        installContainer.className = 'position-fixed bottom-0 end-0 m-3';
        installContainer.style.zIndex = '1040';
        
        // Only show if app is not already installed
        if (window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone === true) {
            return;
        }
        
        installContainer.innerHTML = `
            <button id="manual-install-btn" class="btn btn-primary rounded-pill shadow">
                <i class="fas fa-download me-2"></i>Install App
            </button>
        `;
        
        document.body.appendChild(installContainer);
        
        // Add event listener
        document.getElementById('manual-install-btn').addEventListener('click', triggerInstall);
    };
    
    // Add install button to page
    if ('serviceWorker' in navigator) {
        createInstallButton();
    }
});

// We'll use the global deferredPrompt declared in pwa.js
// No need to add another beforeinstallprompt listener here since it's already in pwa.js

// The triggerInstall function is now defined in pwa.js as window.triggerInstall
// We just provide the manual instructions functionality that's used by the global function

// Show manual install instructions if automatic install isn't available
function showInstallInstructions() {
    // Create a modal with browser-specific instructions
    const browserName = detectBrowser();
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'installInstructionsModal';
    modal.setAttribute('tabindex', '-1');
    modal.setAttribute('aria-labelledby', 'installInstructionsModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-dark">
                <div class="modal-header">
                    <h5 class="modal-title" id="installInstructionsModalLabel">
                        <i class="fas fa-download me-2"></i>Install Dear Teddy
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>To install Dear Teddy on your device:</p>
                    ${getInstructionsForBrowser(browserName)}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Show the modal
    const bsModal = new bootstrap.Modal(document.getElementById('installInstructionsModal'));
    bsModal.show();
}

// Detect browser type
function detectBrowser() {
    const userAgent = navigator.userAgent;
    if (userAgent.indexOf("Chrome") > -1) {
        return "chrome";
    } else if (userAgent.indexOf("Safari") > -1) {
        return "safari";
    } else if (userAgent.indexOf("Firefox") > -1) {
        return "firefox";
    } else if (userAgent.indexOf("MSIE") > -1 || userAgent.indexOf("Trident") > -1) {
        return "ie";
    } else if (userAgent.indexOf("Edge") > -1) {
        return "edge";
    } else {
        return "unknown";
    }
}

// Get browser-specific instructions
function getInstructionsForBrowser(browser) {
    if (browser === "chrome") {
        if (/Android/i.test(navigator.userAgent)) {
            return `
                <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                    <li class="list-group-item bg-transparent">Tap the menu button (⋮) in the top right corner</li>
                    <li class="list-group-item bg-transparent">Select "Add to Home screen"</li>
                    <li class="list-group-item bg-transparent">Confirm by tapping "Add"</li>
                </ol>
            `;
        } else {
            return `
                <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                    <li class="list-group-item bg-transparent">Look for the install icon <i class="fas fa-arrow-alt-circle-down"></i> in the address bar</li>
                    <li class="list-group-item bg-transparent">Click on it and select "Install"</li>
                    <li class="list-group-item bg-transparent">Alternatively, click the menu button (⋮) and select "Install Dear Teddy..."</li>
                </ol>
            `;
        }
    } else if (browser === "safari") {
        return `
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent">Tap the share button <i class="fas fa-share-square"></i> at the bottom of the screen</li>
                <li class="list-group-item bg-transparent">Scroll down and tap "Add to Home Screen"</li>
                <li class="list-group-item bg-transparent">Tap "Add" in the top right corner</li>
            </ol>
        `;
    } else if (browser === "edge") {
        return `
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent">Look for the install icon <i class="fas fa-arrow-alt-circle-down"></i> in the address bar</li>
                <li class="list-group-item bg-transparent">Click it and select "Install"</li>
                <li class="list-group-item bg-transparent">Alternatively, click the menu button (...) and select "Apps" > "Install this site as an app"</li>
            </ol>
        `;
    } else if (browser === "firefox") {
        return `
            <p>Firefox on Android:</p>
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent">Tap the menu button (⋮) in the top right</li>
                <li class="list-group-item bg-transparent">Select "Install" or "Add to Home screen"</li>
            </ol>
            <p class="mt-3">Firefox on desktop may have limited PWA support. For the best experience, try using Chrome, Edge, or Safari.</p>
        `;
    } else {
        return `
            <p>General instructions:</p>
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent">Look for "Add to Home Screen" or "Install" in your browser's menu</li>
                <li class="list-group-item bg-transparent">On mobile, this is often found in the share menu</li>
                <li class="list-group-item bg-transparent">On desktop, look for an install icon in the address bar or browser menu</li>
            </ol>
            <p class="mt-3">For the best experience, we recommend using Chrome, Edge, or Safari.</p>
        `;
    }
}