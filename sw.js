const CACHE_NAME = 'synocast-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/styles/style.css',
  '/assets/js/weather.js',
  '/assets/logo/logo.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    }).catch(() => {
      // Return offline fallback if needed
    })
  );
});
