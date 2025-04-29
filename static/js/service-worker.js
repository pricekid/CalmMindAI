
const CACHE_NAME = 'calm-journey-v1';
const urlsToCache = [
  '/',
  '/static/css/custom.css',
  '/static/js/reflection-handler.js',
  '/static/images/logo.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
