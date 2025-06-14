// Install button functionality for Dear Teddy PWA

document.addEventListener('DOMContentLoaded', () => {
    // Install button functionality disabled
    // No automatic install buttons will be created
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
                <div class="modal-header border-secondary">
                    <h5 class="modal-title text-light" id="installInstructionsModalLabel">
                        <i class="fas fa-download me-2"></i>Install Dear Teddy
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body text-light">
                    <p class="text-light">To install Dear Teddy on your device:</p>
                    ${getInstructionsForBrowser(browserName)}
                </div>
                <div class="modal-footer border-secondary">
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
                    <li class="list-group-item bg-transparent text-white border-secondary">Tap the menu button (⋮) in the top right corner</li>
                    <li class="list-group-item bg-transparent text-white border-secondary">Select "Add to Home screen"</li>
                    <li class="list-group-item bg-transparent text-white border-secondary">Confirm by tapping "Add"</li>
                </ol>
            `;
        } else {
            return `
                <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                    <li class="list-group-item bg-transparent text-white border-secondary">Look for the install icon <i class="fas fa-arrow-alt-circle-down"></i> in the address bar</li>
                    <li class="list-group-item bg-transparent text-white border-secondary">Click on it and select "Install"</li>
                    <li class="list-group-item bg-transparent text-white border-secondary">Alternatively, click the menu button (⋮) and select "Install Dear Teddy..."</li>
                </ol>
            `;
        }
    } else if (browser === "safari") {
        return `
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent text-white border-secondary">Tap the share button <i class="fas fa-share-square"></i> at the bottom of the screen</li>
                <li class="list-group-item bg-transparent text-white border-secondary">Scroll down and tap "Add to Home Screen"</li>
                <li class="list-group-item bg-transparent text-white border-secondary">Tap "Add" in the top right corner</li>
            </ol>
        `;
    } else if (browser === "edge") {
        return `
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent text-white border-secondary">Look for the install icon <i class="fas fa-arrow-alt-circle-down"></i> in the address bar</li>
                <li class="list-group-item bg-transparent text-white border-secondary">Click it and select "Install"</li>
                <li class="list-group-item bg-transparent text-white border-secondary">Alternatively, click the menu button (...) and select "Apps" > "Install this site as an app"</li>
            </ol>
        `;
    } else if (browser === "firefox") {
        return `
            <p>Firefox on Android:</p>
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent text-white border-secondary">Tap the menu button (⋮) in the top right</li>
                <li class="list-group-item bg-transparent text-white border-secondary">Select "Install" or "Add to Home screen"</li>
            </ol>
            <p class="mt-3 text-white">Firefox on desktop may have limited PWA support. For the best experience, try using Chrome, Edge, or Safari.</p>
        `;
    } else {
        return `
            <p class="text-white">General instructions:</p>
            <ol class="list-group list-group-numbered list-group-flush bg-transparent">
                <li class="list-group-item bg-transparent text-white border-secondary">Look for "Add to Home Screen" or "Install" in your browser's menu</li>
                <li class="list-group-item bg-transparent text-white border-secondary">On mobile, this is often found in the share menu</li>
                <li class="list-group-item bg-transparent text-white border-secondary">On desktop, look for an install icon in the address bar or browser menu</li>
            </ol>
            <p class="mt-3 text-white">For the best experience, we recommend using Chrome, Edge, or Safari.</p>
        `;
    }
}