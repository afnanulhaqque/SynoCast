const CACHE_NAME = 'synocast-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/styles/style.css',
  '/assets/js/weather.js',
  '/assets/logo/logo-small.png',
  '/assets/logo/icon-512.png'
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

self.addEventListener('push', function(event) {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/assets/logo/icon-512.png',
      badge: '/assets/logo/logo-small.png',
      data: {
        url: data.url || '/'
      }
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url)
  );
});
