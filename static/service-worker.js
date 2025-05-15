// Dear Teddy Service Worker
// This service worker handles push notifications and caching for PWA support

const CACHE_NAME = 'dearteddy-v1';
const urlsToCache = [
  '/',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/js/push-notifications.js',
  '/static/images/logo.svg',
  '/static/favicon.ico'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker caching app shell...');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== CACHE_NAME) {
          console.log('Service Worker removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  return self.clients.claim();
});

// Fetch event - serve from cache if available, otherwise fetch from network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Cache hit - return the response from the cached version
        if (response) {
          return response;
        }
        
        // Not in cache - fetch from network
        return fetch(event.request).then((networkResponse) => {
          // Don't cache responses with error status codes
          if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
            return networkResponse;
          }
          
          // Clone the response as it's a stream and can only be consumed once
          const responseToCache = networkResponse.clone();
          
          // Add response to cache for future
          caches.open(CACHE_NAME)
            .then((cache) => {
              cache.put(event.request, responseToCache);
            });
            
          return networkResponse;
        });
      })
  );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  let data = {};
  if (event.data) {
    try {
      data = event.data.json();
    } catch(e) {
      console.error('Error parsing push notification data:', e);
      data = {
        title: 'Dear Teddy',
        message: 'New notification from Dear Teddy',
        icon: '/static/images/logo.svg'
      };
    }
  }
  
  // Default notification options
  const title = data.title || 'Dear Teddy';
  const options = {
    body: data.message || 'You have a new notification',
    icon: data.icon || '/static/images/logo.svg',
    badge: '/static/images/logo-small.svg',
    tag: data.tag || 'dearteddy-notification',
    data: {
      url: data.url || '/'
    }
  };
  
  // Show the notification
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click event - handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();
  
  // Get the URL from the notification data
  const url = event.notification.data.url || '/';
  
  // Open or focus the app
  event.waitUntil(
    clients.matchAll({type: 'window'})
      .then((clientList) => {
        // Check if there's already a window/tab open with the target URL
        for (const client of clientList) {
          if (client.url === url && 'focus' in client)
            return client.focus();
        }
        // If not, open a new window/tab
        if (clients.openWindow)
          return clients.openWindow(url);
      })
  );
});