const CACHE_NAME = 'synocast-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/static/styles/style.css',
  '/assets/js/weather.js',
  '/assets/js/location_handler.js',
  '/assets/js/weather_utils.js',
  '/assets/js/map.js',
  '/assets/js/chatbot_modal.js',
  '/assets/js/subscribe_modal.js',
  '/assets/js/periodic_sync.js',
  '/assets/logo/logo_about.png',
  '/offline'
];

// Import periodic sync functionality
importScripts('/assets/js/periodic_sync.js');

self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching assets');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  // Force the waiting service worker to become the active service worker
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  // Claim all clients immediately
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Network-first strategy for API calls
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone the response before caching
          const responseClone = response.clone();
          
          // Cache successful API responses
          if (response.ok) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[SW] Serving API from cache:', url.pathname);
              return cachedResponse;
            }
            // Return offline response for failed API calls
            return new Response(
              JSON.stringify({ error: 'Offline', cached: false }),
              {
                headers: { 'Content-Type': 'application/json' },
                status: 503
              }
            );
          });
        })
    );
    return;
  }

  // Cache-first strategy for static assets
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(request)
        .then((response) => {
          // Don't cache non-successful responses
          if (!response || response.status !== 200 || response.type === 'error') {
            return response;
          }

          // Clone the response
          const responseToCache = response.clone();

          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });

          return response;
        })
        .catch(() => {
          // Return offline page for navigation requests
          if (request.mode === 'navigate') {
            return caches.match('/offline');
          }
          return new Response('Offline', { status: 503 });
        });
    })
  );
});

// Handle push notifications
self.addEventListener('push', function(event) {
  console.log('[SW] Push notification received');
  
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/assets/logo/logo_about.png',
      badge: '/assets/logo/logo-small.png',
      vibrate: [200, 100, 200],
      data: {
        url: data.url || '/',
        timestamp: Date.now()
      },
      actions: [
        {
          action: 'view',
          title: 'View Details'
        },
        {
          action: 'dismiss',
          title: 'Dismiss'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// Handle notification clicks (already defined in periodic_sync.js but keeping for compatibility)
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  
  const action = event.action;
  const url = event.notification.data.url || '/';
  
  if (action === 'dismiss') {
    return;
  }
  
  event.waitUntil(
    clients.openWindow(url)
  );
});

// Handle background sync for queued actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync event:', event.tag);
  
  if (event.tag === 'sync-favorites') {
    event.waitUntil(syncFavorites());
  } else if (event.tag === 'sync-preferences') {
    event.waitUntil(syncPreferences());
  }
});

/**
 * Sync queued favorite locations
 */
async function syncFavorites() {
  try {
    const queue = await getQueuedActions('favorites');
    
    for (const action of queue) {
      const response = await fetch('/api/user/favorites', {
        method: action.method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action.data)
      });
      
      if (response.ok) {
        await removeFromQueue('favorites', action.id);
      }
    }
  } catch (error) {
    console.error('[SW] Favorite sync failed:', error);
  }
}

/**
 * Sync queued preference updates
 */
async function syncPreferences() {
  try {
    const queue = await getQueuedActions('preferences');
    
    for (const action of queue) {
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(action.data)
      });
      
      if (response.ok) {
        await removeFromQueue('preferences', action.id);
      }
    }
  } catch (error) {
    console.error('[SW] Preferences sync failed:', error);
  }
}

/**
 * Get queued actions from IndexedDB
 */
async function getQueuedActions(queueName) {
  return new Promise((resolve) => {
    const request = indexedDB.open('SynoCastDB', 1);
    
    request.onsuccess = () => {
      const db = request.result;
      
      if (!db.objectStoreNames.contains('syncQueue')) {
        resolve([]);
        return;
      }
      
      const transaction = db.transaction(['syncQueue'], 'readonly');
      const store = transaction.objectStore('syncQueue');
      const index = store.index('queueName');
      const getRequest = index.getAll(queueName);
      
      getRequest.onsuccess = () => resolve(getRequest.result || []);
      getRequest.onerror = () => resolve([]);
    };
    
    request.onerror = () => resolve([]);
  });
}

/**
 * Remove action from sync queue
 */
async function removeFromQueue(queueName, actionId) {
  return new Promise((resolve) => {
    const request = indexedDB.open('SynoCastDB', 1);
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['syncQueue'], 'readwrite');
      const store = transaction.objectStore('syncQueue');
      
      store.delete(actionId);
      
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => resolve();
    };
    
    request.onerror = () => resolve();
  });
}
