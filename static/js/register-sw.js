// Register Service Worker for PWA and Push Notifications
document.addEventListener('DOMContentLoaded', function() {
  console.log('Checking for Service Worker support...');
  
  if ('serviceWorker' in navigator) {
    console.log('Service Worker is supported');
    
    // Register the service worker
    navigator.serviceWorker.register('/static/service-worker.js')
      .then(function(registration) {
        console.log('Service Worker registered with scope:', registration.scope);
        
        // Refresh the service worker if needed
        if (registration.active) {
          registration.update();
        }
      })
      .catch(function(error) {
        console.error('Service Worker registration failed:', error);
      });
      
    // Check for updates to the service worker
    navigator.serviceWorker.addEventListener('controllerchange', function() {
      console.log('Service Worker controller changed');
    });
  } else {
    console.log('Service Worker is not supported in this browser');
  }
});