/**
 * Offline Storage Module for SynoCast
 * Handles IndexedDB operations for weather data persistence
 */

const DB_NAME = 'SynoCastDB';
const DB_VERSION = 1;

class OfflineStorage {
    constructor() {
        this.db = null;
        this.initDB();
    }

    /**
     * Initialize IndexedDB database
     */
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('[OfflineStorage] Database error:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('[OfflineStorage] Database initialized');
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Weather cache store
                if (!db.objectStoreNames.contains('weatherCache')) {
                    const weatherStore = db.createObjectStore('weatherCache', { keyPath: 'id' });
                    weatherStore.createIndex('timestamp', 'timestamp', { unique: false });
                    weatherStore.createIndex('location', ['lat', 'lon'], { unique: false });
                }

                // Favorites store
                if (!db.objectStoreNames.contains('favorites')) {
                    const favStore = db.createObjectStore('favorites', { keyPath: 'id', autoIncrement: true });
                    favStore.createIndex('location', ['lat', 'lon'], { unique: true });
                    favStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Settings store
                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings');
                }

                // Sync queue store
                if (!db.objectStoreNames.contains('syncQueue')) {
                    const queueStore = db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
                    queueStore.createIndex('queueName', 'queueName', { unique: false });
                    queueStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                console.log('[OfflineStorage] Database schema created');
            };
        });
    }

    /**
     * Store weather data
     */
    async storeWeatherData(lat, lon, data) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['weatherCache'], 'readwrite');
            const store = transaction.objectStore('weatherCache');

            const cacheEntry = {
                id: `weather_${lat}_${lon}`,
                lat: parseFloat(lat),
                lon: parseFloat(lon),
                data: data,
                timestamp: Date.now()
            };

            const request = store.put(cacheEntry);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Weather data stored');
                resolve();
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Store error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get cached weather data
     */
    async getWeatherData(lat, lon, maxAge = 24 * 60 * 60 * 1000) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['weatherCache'], 'readonly');
            const store = transaction.objectStore('weatherCache');
            const request = store.get(`weather_${lat}_${lon}`);

            request.onsuccess = () => {
                const result = request.result;

                if (!result) {
                    resolve(null);
                    return;
                }

                // Check if data is still fresh
                const age = Date.now() - result.timestamp;
                if (age > maxAge) {
                    console.log('[OfflineStorage] Cached data expired');
                    resolve(null);
                    return;
                }

                console.log('[OfflineStorage] Retrieved cached weather data');
                resolve({
                    ...result.data,
                    cached: true,
                    cacheAge: age
                });
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Retrieval error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Store favorite location
     */
    async addFavorite(location) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['favorites'], 'readwrite');
            const store = transaction.objectStore('favorites');

            const favorite = {
                ...location,
                timestamp: Date.now()
            };

            const request = store.add(favorite);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Favorite added');
                resolve(request.result);
            };

            request.onerror = () => {
                // Check if it's a duplicate
                if (request.error.name === 'ConstraintError') {
                    console.log('[OfflineStorage] Favorite already exists');
                    resolve(null);
                } else {
                    console.error('[OfflineStorage] Add favorite error:', request.error);
                    reject(request.error);
                }
            };
        });
    }

    /**
     * Get all favorites
     */
    async getFavorites() {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['favorites'], 'readonly');
            const store = transaction.objectStore('favorites');
            const request = store.getAll();

            request.onsuccess = () => {
                console.log('[OfflineStorage] Retrieved favorites');
                resolve(request.result || []);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Get favorites error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Remove favorite
     */
    async removeFavorite(id) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['favorites'], 'readwrite');
            const store = transaction.objectStore('favorites');
            const request = store.delete(id);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Favorite removed');
                resolve();
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Remove favorite error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Store setting
     */
    async setSetting(key, value) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['settings'], 'readwrite');
            const store = transaction.objectStore('settings');
            const request = store.put(value, key);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Setting stored:', key);
                resolve();
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Store setting error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get setting
     */
    async getSetting(key) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['settings'], 'readonly');
            const store = transaction.objectStore('settings');
            const request = store.get(key);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Get setting error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Queue action for background sync
     */
    async queueAction(queueName, method, data) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['syncQueue'], 'readwrite');
            const store = transaction.objectStore('syncQueue');

            const action = {
                queueName: queueName,
                method: method,
                data: data,
                timestamp: Date.now()
            };

            const request = store.add(action);

            request.onsuccess = () => {
                console.log('[OfflineStorage] Action queued for sync');
                resolve(request.result);
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Queue action error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Clear old cached data
     */
    async clearOldCache(maxAge = 7 * 24 * 60 * 60 * 1000) {
        if (!this.db) await this.initDB();

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['weatherCache'], 'readwrite');
            const store = transaction.objectStore('weatherCache');
            const index = store.index('timestamp');
            const cutoffTime = Date.now() - maxAge;

            const request = index.openCursor();
            let deletedCount = 0;

            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    if (cursor.value.timestamp < cutoffTime) {
                        cursor.delete();
                        deletedCount++;
                    }
                    cursor.continue();
                } else {
                    console.log(`[OfflineStorage] Cleared ${deletedCount} old cache entries`);
                    resolve(deletedCount);
                }
            };

            request.onerror = () => {
                console.error('[OfflineStorage] Clear cache error:', request.error);
                reject(request.error);
            };
        });
    }

    /**
     * Get cache size estimate
     */
    async getCacheSize() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            const estimate = await navigator.storage.estimate();
            return {
                usage: estimate.usage,
                quota: estimate.quota,
                percentage: (estimate.usage / estimate.quota * 100).toFixed(2)
            };
        }
        return null;
    }
}

// Create singleton instance
const offlineStorage = new OfflineStorage();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = offlineStorage;
}
