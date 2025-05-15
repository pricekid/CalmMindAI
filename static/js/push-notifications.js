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

// Subscribe to push notifications
async function subscribeToPushNotifications() {
  // Check if push is supported
  if (!isPushSupported()) {
    console.log('Push notifications not supported');
    showNotificationMessage('error', 'Your browser does not support push notifications');
    return false;
  }
  
  try {
    // Get the service worker registration
    const registration = await navigator.serviceWorker.ready;
    
    // Get the public key
    const publicKey = await getPublicKey();
    if (!publicKey) {
      showNotificationMessage('error', 'Push notification system is not configured');
      return false;
    }
    
    // Convert public key to the correct format
    const applicationServerKey = urlBase64ToUint8Array(publicKey);
    
    // Check existing subscriptions
    let subscription = await registration.pushManager.getSubscription();
    
    // If already subscribed, return the existing subscription
    if (subscription) {
      console.log('Already subscribed to push notifications');
      await sendSubscriptionToServer(subscription);
      return subscription;
    }
    
    // Otherwise, subscribe
    subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    });
    
    console.log('Push notification subscription successful');
    
    // Send subscription to the server
    const saved = await sendSubscriptionToServer(subscription);
    if (saved) {
      showNotificationMessage('success', 'Successfully subscribed to push notifications');
    }
    
    return subscription;
  } catch (err) {
    console.error('Error subscribing to push notifications:', err);
    
    // Handle permission denied error
    if (Notification.permission === 'denied') {
      showNotificationMessage('error', 'Notification permission denied. Please enable notifications in your browser settings.');
    } else {
      showNotificationMessage('error', 'Failed to subscribe to push notifications');
    }
    
    return null;
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
    
    // Check if notifications are already granted
    if (Notification.permission === 'granted') {
      // Add a button to the dashboard to enable push
      const enableContainer = document.getElementById('push-notification-container');
      if (enableContainer) {
        enableContainer.innerHTML = `
          <div class="card bg-dark my-3">
            <div class="card-body">
              <h5 class="card-title"><i class="fas fa-bell me-2"></i>Real-time Notifications</h5>
              <p class="card-text">Get instant notifications for journal reminders, mood tracking, and app updates.</p>
              <button id="enable-push-btn" class="btn btn-primary">Enable Notifications</button>
            </div>
          </div>
        `;
        
        const enableButton = document.getElementById('enable-push-btn');
        if (enableButton) {
          enableButton.addEventListener('click', async () => {
            const subscription = await subscribeToPushNotifications();
            if (subscription) {
              enableContainer.innerHTML = `
                <div class="alert alert-success">
                  <i class="fas fa-check-circle me-2"></i>Push notifications are enabled!
                  <button id="test-push-btn" class="btn btn-sm btn-primary ms-2">Test Notification</button>
                </div>
              `;
              
              const testPushBtn = document.getElementById('test-push-btn');
              if (testPushBtn) {
                testPushBtn.addEventListener('click', testPushNotification);
              }
            }
          });
        }
      }
    }
  });
}

// Initialize
initPushUI();

// Expose functions globally
window.subscribeToPushNotifications = subscribeToPushNotifications;
window.testPushNotification = testPushNotification;