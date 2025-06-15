// Push Notification Handler for Dear Teddy
// This script manages push notification subscriptions

// Check if the browser supports push notifications
function isPushSupported() {
  return 'serviceWorker' in navigator && 'PushManager' in window;
}

// Convert a base64 string to a Uint8Array for the push subscription
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

// Get the server's public VAPID key
async function getPublicKey() {
  try {
    const response = await fetch('/push-key');
    const data = await response.json();
    
    if (data.error) {
      console.error('Error getting public key:', data.error);
      return null;
    }
    
    return data.public_key;
  } catch (err) {
    console.error('Failed to get public key:', err);
    return null;
  }
}

// Send the push subscription to the server
async function sendSubscriptionToServer(subscription) {
  try {
    const response = await fetch('/push-subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(subscription),
    });
    
    const data = await response.json();
    if (response.ok) {
      console.log('Push subscription saved successfully');
      return true;
    } else {
      console.error('Failed to save subscription:', data.error);
      return false;
    }
  } catch (err) {
    console.error('Error sending subscription to server:', err);
    return false;
  }
}

// Subscribe to push notifications (simplified version that doesn't require service worker)
async function subscribeToPushNotifications() {
  console.log('Requesting notification permission...');
  
  try {
    // Simple approach - just request notification permission
    if (!("Notification" in window)) {
      console.log('Notifications not supported');
      showNotificationMessage('error', 'Your browser does not support notifications');
      return false;
    }
    
    // Check if already granted
    if (Notification.permission === "granted") {
      console.log('Notification permission already granted');
      showNotificationMessage('success', 'Notifications are already enabled!');
      return true;
    }
    
    // Check if denied
    if (Notification.permission === "denied") {
      console.log('Notification permission denied');
      showNotificationMessage('error', 'Notification permission denied. Please enable notifications in your browser settings.');
      return false;
    }
    
    // Request permission
    const permission = await Notification.requestPermission();
    
    if (permission === "granted") {
      console.log('Notification permission granted');
      showNotificationMessage('success', 'Successfully enabled notifications!');
      
      // Send a test notification
      setTimeout(() => {
        const notification = new Notification('Dear Teddy', {
          body: 'Notifications are now enabled!',
          icon: '/static/images/teddy-icon.svg'
        });
        
        notification.onclick = function() {
          window.focus();
          notification.close();
        };
      }, 2000);
      
      return true;
    } else {
      console.log('Notification permission denied or dismissed');
      showNotificationMessage('error', 'Notification permission was not granted.');
      return false;
    }
  } catch (err) {
    console.error('Error requesting notification permission:', err);
    showNotificationMessage('error', 'Failed to request notification permission');
    return false;
  }
}

// Function to show UI notification message
function showNotificationMessage(type, message) {
  // Create notification element if it doesn't exist
  let notification = document.getElementById('notification-message');
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'notification-message';
    notification.className = 'alert alert-dismissible fade show position-fixed bottom-0 end-0 m-3';
    notification.style.zIndex = '1060';
    notification.innerHTML = `
      <span class="message"></span>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(notification);
  }
  
  // Set class based on notification type
  notification.className = 'alert alert-dismissible fade show position-fixed bottom-0 end-0 m-3';
  if (type === 'success') {
    notification.classList.add('alert-success');
  } else if (type === 'error') {
    notification.classList.add('alert-danger');
  } else {
    notification.classList.add('alert-info');
  }
  
  // Set the message
  notification.querySelector('.message').textContent = message;
  
  // Show the notification
  const bsAlert = new bootstrap.Alert(notification);
  
  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    try {
      bsAlert.close();
    } catch (e) {
      notification.remove();
    }
  }, 5000);
}

// Function to test push notifications
async function testPushNotification() {
  try {
    const response = await fetch('/push-test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    const data = await response.json();
    if (response.ok) {
      showNotificationMessage('success', data.message);
      return true;
    } else {
      showNotificationMessage('error', data.error || 'Failed to send test notification');
      return false;
    }
  } catch (err) {
    console.error('Error sending test notification:', err);
    showNotificationMessage('error', 'Failed to send test notification');
    return false;
  }
}

// Function to automatically request notification permission (simplified version)
async function autoRequestPushPermission() {
  console.log('Auto-request function called');
  
  // First check if permission is already granted
  if (Notification.permission === 'granted') {
    console.log('Notification permission already granted');
    return true;
  }
  
  // If permission hasn't been denied yet, request it
  if (Notification.permission !== 'denied') {
    // Request permission automatically
    console.log('Automatically requesting notification permission');
    try {
      // Use the simplified subscribe function
      await subscribeToPushNotifications();
      return true;
    } catch (err) {
      console.error('Failed to auto-request notification permission:', err);
      return false;
    }
  }
  
  // If we reach here, permission is denied
  console.log('Notification permission previously denied');
  return false;
}

// Initialize push notification subscription UI
function initPushUI() {
  // Wait for DOM to be ready
  document.addEventListener('DOMContentLoaded', () => {
    // Add notification subscribe button if it exists
    const subscribeButton = document.getElementById('push-subscribe-btn');
    if (subscribeButton) {
      subscribeButton.addEventListener('click', subscribeToPushNotifications);
    }
    
    // Add test notification button if it exists
    const testButton = document.getElementById('push-test-btn');
    if (testButton) {
      testButton.addEventListener('click', testPushNotification);
    }
    
    // Check if on dashboard page
    const enableContainer = document.getElementById('push-notification-container');
    if (enableContainer) {
      // Set up UI based on notification permission status
      const updateNotificationUI = async () => {
        if (Notification.permission === 'granted') {
          // Show success message
          enableContainer.innerHTML = `
            <div class="card dashboard-widget" style="background-color: #ffffff; border: 1px solid #dee2e6;">
              <div class="card-header" style="background-color: #1D4D4F; color: #ffffff;">
                <h3 class="mb-0"><i class="fas fa-bell me-2"></i> Stay Connected</h3>
              </div>
              <div class="card-body p-3">
                <div class="alert alert-success" style="background-color: #d4edda; border-color: #c3e6cb; color: #155724;">
                  <i class="fas fa-check-circle me-2"></i><strong style="color: #155724;">Push notifications are enabled!</strong>
                  <p class="mt-2 mb-0" style="color: #155724;">You'll receive timely reminders for journal prompts, mood tracking, and app updates.</p>
                  <button id="test-push-btn" class="btn btn-sm btn-outline-success mt-2">Test Notification</button>
                </div>
              </div>
            </div>
          `;
          
          const testPushBtn = document.getElementById('test-push-btn');
          if (testPushBtn) {
            testPushBtn.addEventListener('click', testPushNotification);
          }
        } else {
          // Show enable button
          enableContainer.innerHTML = `
            <div class="card dashboard-widget" style="background-color: #ffffff; border: 1px solid #dee2e6;">
              <div class="card-header" style="background-color: #1D4D4F; color: #ffffff;">
                <h3 class="mb-0"><i class="fas fa-bell me-2"></i> Stay Connected</h3>
              </div>
              <div class="card-body p-3">
                <div class="row">
                  <div class="col-md-8">
                    <p style="color: #000000 !important; font-weight: 600 !important; text-shadow: none !important;">Enable notifications to get timely reminders for:</p>
                    <ul class="list-unstyled">
                      <li><i class="fas fa-check-circle text-success me-2"></i><span style="color: #000000 !important; font-weight: 600 !important; text-shadow: none !important;">Daily journal prompts</span></li>
                      <li><i class="fas fa-check-circle text-success me-2"></i><span style="color: #000000 !important; font-weight: 600 !important; text-shadow: none !important;">Mood tracking reminders</span></li>
                      <li><i class="fas fa-check-circle text-success me-2"></i><span style="color: #000000 !important; font-weight: 600 !important; text-shadow: none !important;">New features and updates</span></li>
                    </ul>
                    <p style="color: #000000 !important; font-weight: 500 !important; text-shadow: none !important;" class="small">You can customize notification settings at any time.</p>
                    <div class="d-flex gap-2 mt-3">
                      <a href="/push-settings" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-cog me-1"></i>Notification Settings
                      </a>
                      <a href="/journal-reminder-settings" class="btn btn-sm btn-outline-secondary">
                        <i class="fas fa-clock me-1"></i>Journal Reminders
                      </a>
                    </div>
                  </div>
                  <div class="col-md-4 d-flex align-items-center justify-content-center">
                    <button id="enable-push-btn" class="btn btn-lg" style="background: linear-gradient(45deg, #A05C2C, #d1a673); border: none; color: #ffffff; font-weight: 600;">
                      <i class="fas fa-bell me-2"></i>Enable Notifications
                    </button>
                  </div>
                </div>
              </div>
            </div>
          `;
          
          const enableButton = document.getElementById('enable-push-btn');
          if (enableButton) {
            enableButton.addEventListener('click', async () => {
              const subscription = await subscribeToPushNotifications();
              if (subscription) {
                updateNotificationUI();
              }
            });
          }
        }
      };
      
      // Initial UI setup
      updateNotificationUI();
      
      // Auto-request permission after a short delay (gives page time to load)
      setTimeout(() => {
        // Only auto-request if we're not sure about permission
        if (Notification.permission === 'default') {
          autoRequestPushPermission().then(updateNotificationUI);
        }
      }, 3000);
    }
  });
}

// Initialize
initPushUI();

// Expose functions globally
window.subscribeToPushNotifications = subscribeToPushNotifications;
window.testPushNotification = testPushNotification;