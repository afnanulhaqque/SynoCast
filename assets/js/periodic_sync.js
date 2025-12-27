/**
 * Periodic Background Sync for SynoCast
 * Handles periodic weather updates and push notifications
 */

const SYNC_INTERVAL = 60 * 60 * 1000; // 60 minutes in milliseconds
const SYNC_TAG = 'weather-sync';

// Register periodic sync when service worker is activated
self.addEventListener('activate', async (event) => {
    console.log('[Periodic Sync] Service worker activated');
    
    // Request periodic sync permission
    if ('periodicSync' in self.registration) {
        try {
            await self.registration.periodicSync.register(SYNC_TAG, {
                minInterval: SYNC_INTERVAL
            });
            console.log('[Periodic Sync] Registered successfully');
        } catch (error) {
            console.warn('[Periodic Sync] Registration failed:', error);
        }
    } else {
        console.warn('[Periodic Sync] Not supported in this browser');
    }
});

// Handle periodic sync events
self.addEventListener('periodicsync', (event) => {
    console.log('[Periodic Sync] Event triggered:', event.tag);
    
    if (event.tag === SYNC_TAG) {
        event.waitUntil(syncWeatherData());
    }
});

/**
 * Fetch and cache latest weather data, then send notification if needed
 */
async function syncWeatherData() {
    try {
        console.log('[Periodic Sync] Starting weather data sync...');
        
        // Get stored location from IndexedDB
        const location = await getStoredLocation();
        
        if (!location || !location.lat || !location.lon) {
            console.warn('[Periodic Sync] No location found, skipping sync');
            return;
        }

        // Fetch compact weather data
        const response = await fetch(
            `/api/widget-data?lat=${location.lat}&lon=${location.lon}`
        );

        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }

        const weatherData = await response.json();
        
        // Store in IndexedDB for offline access
        await storeWeatherData(weatherData);
        
        // Check if we should send a notification
        const shouldNotify = await checkNotificationCriteria(weatherData);
        
        if (shouldNotify) {
            await sendWeatherNotification(weatherData);
        }
        
        console.log('[Periodic Sync] Weather data synced successfully');
        
    } catch (error) {
        console.error('[Periodic Sync] Sync failed:', error);
    }
}

/**
 * Get stored location from IndexedDB
 */
async function getStoredLocation() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('SynoCastDB', 1);
        
        request.onerror = () => reject(request.error);
        
        request.onsuccess = () => {
            const db = request.result;
            
            if (!db.objectStoreNames.contains('settings')) {
                resolve(null);
                return;
            }
            
            const transaction = db.transaction(['settings'], 'readonly');
            const store = transaction.objectStore('settings');
            const getRequest = store.get('lastLocation');
            
            getRequest.onsuccess = () => resolve(getRequest.result);
            getRequest.onerror = () => reject(getRequest.error);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('settings')) {
                db.createObjectStore('settings');
            }
        };
    });
}

/**
 * Store weather data in IndexedDB
 */
async function storeWeatherData(data) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('SynoCastDB', 1);
        
        request.onerror = () => reject(request.error);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['weatherCache'], 'readwrite');
            const store = transaction.objectStore('weatherCache');
            
            const cacheEntry = {
                id: 'current',
                data: data,
                timestamp: Date.now()
            };
            
            store.put(cacheEntry);
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('weatherCache')) {
                db.createObjectStore('weatherCache', { keyPath: 'id' });
            }
        };
    });
}

/**
 * Check if notification should be sent based on weather conditions
 */
async function checkNotificationCriteria(weatherData) {
    // Get last notification time
    const lastNotificationTime = await getLastNotificationTime();
    const now = Date.now();
    
    // Don't send notifications more than once per hour
    if (lastNotificationTime && (now - lastNotificationTime) < 60 * 60 * 1000) {
        return false;
    }
    
    const weather = weatherData.current;
    
    // Send notification for significant weather conditions
    const significantConditions = [
        'Rain', 'Thunderstorm', 'Snow', 'Drizzle', 'Extreme'
    ];
    
    if (significantConditions.includes(weather.weather.main)) {
        return true;
    }
    
    // Send notification for extreme temperatures
    if (weather.temp > 35 || weather.temp < 0) {
        return true;
    }
    
    // Send notification for high humidity (>85%)
    if (weather.humidity > 85) {
        return true;
    }
    
    return false;
}

/**
 * Send rich weather notification
 */
async function sendWeatherNotification(weatherData) {
    const { location, current } = weatherData;
    
    // Get weather icon
    const iconUrl = `/assets/logo/icon-512.png`;
    
    // Create notification title and body
    const title = `${current.temp}°C in ${location.city}`;
    const body = `${current.weather.description}. Feels like ${current.feels_like}°C`;
    
    // Notification options with actions
    const options = {
        body: body,
        icon: iconUrl,
        badge: '/assets/logo/logo-small.png',
        tag: 'weather-update',
        requireInteraction: false,
        vibrate: [200, 100, 200],
        data: {
            url: '/weather',
            timestamp: Date.now(),
            weather: current
        },
        actions: [
            {
                action: 'view',
                title: 'View Forecast',
                icon: '/assets/logo/logo-small.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ]
    };
    
    // Show notification
    await self.registration.showNotification(title, options);
    
    // Update last notification time
    await setLastNotificationTime(Date.now());
}

/**
 * Get last notification timestamp
 */
async function getLastNotificationTime() {
    return new Promise((resolve) => {
        const request = indexedDB.open('SynoCastDB', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            
            if (!db.objectStoreNames.contains('settings')) {
                resolve(null);
                return;
            }
            
            const transaction = db.transaction(['settings'], 'readonly');
            const store = transaction.objectStore('settings');
            const getRequest = store.get('lastNotificationTime');
            
            getRequest.onsuccess = () => resolve(getRequest.result);
            getRequest.onerror = () => resolve(null);
        };
        
        request.onerror = () => resolve(null);
    });
}

/**
 * Set last notification timestamp
 */
async function setLastNotificationTime(timestamp) {
    return new Promise((resolve) => {
        const request = indexedDB.open('SynoCastDB', 1);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['settings'], 'readwrite');
            const store = transaction.objectStore('settings');
            
            store.put(timestamp, 'lastNotificationTime');
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => resolve();
        };
        
        request.onerror = () => resolve();
    });
}

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/weather')
        );
    } else if (event.action === 'dismiss') {
        // Just close the notification
        return;
    } else {
        // Default action - open the app
        event.waitUntil(
            clients.openWindow('/weather')
        );
    }
});
