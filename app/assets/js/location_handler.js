/**
 * Universal Location Handler for SynoCast
 * This script handles checking for location permissions and showing the custom modal
 * across all pages of the application.
 * 
 * Features:
 * - Location permission management
 * - Automatic location monitoring with watchPosition
 * - Auto-refresh weather on significant location changes (>5km)
 * - Debounced updates to prevent excessive API calls
 */

// Configuration
const LOCATION_UPDATE_THRESHOLD_KM = 5; // Minimum distance change to trigger update
const UPDATE_DEBOUNCE_MS = 30000; // 30 seconds debounce
let locationWatchId = null;
let lastUpdateTime = 0;
let autoUpdateEnabled = true; // Can be controlled by user preferences

document.addEventListener('DOMContentLoaded', function () {
    const hasLocation = sessionStorage.getItem('synocast_location_fixed');
    const modalEl = document.getElementById('locationPermissionModal');
    if (!modalEl) return;

    const modal = new bootstrap.Modal(modalEl);

    // Initial check
    checkLocationStatus();

    async function checkLocationStatus() {
        if (!navigator.geolocation) return;

        // Check for cached location (60 minutes)
        const cachedLoc = JSON.parse(localStorage.getItem('synocast_cached_location'));
        const now = new Date().getTime();
        const hasPermissionHint = localStorage.getItem('synocast_permission_hint') === 'true';

        if (cachedLoc && (now - cachedLoc.timestamp < 3600000)) {
            window.synocast_current_loc = { lat: cachedLoc.lat, lon: cachedLoc.lon, isCached: true };
            setTimeout(() => {
                window.dispatchEvent(new CustomEvent('synocast_location_granted', {
                    detail: window.synocast_current_loc
                }));
            }, 100);

            // If we have a permission hint, we can try to refresh silently
            if (hasPermissionHint) {
                refreshLocationSilently();
            }
        } else {
            // No valid cache. We show our custom modal INSTEAD of calling any browser API
            // to avoid the native prompt on page load.
            setTimeout(async () => {
                if (!window.synocast_current_loc) {
                    // Try IP-based location first if no local permission
                    const hasPermissionHint = localStorage.getItem('synocast_permission_hint') === 'true';
                    if (!hasPermissionHint) {
                        try {
                            const ipRes = await fetch('/api/ip-location');
                            const ipData = await ipRes.json();
                            if (ipData.status === 'success') {
                                console.log("Using IP-based location fallback:", ipData.city);
                                dispatchLocationEvent(ipData.lat, ipData.lon, true);
                            } else {
                                modal.show();
                            }
                        } catch (err) {
                            console.warn("IP-based fallback failed:", err);
                            modal.show();
                        }
                    } else {
                        modal.show();
                    }
                }
            }, 1500);
        }
    }

    function refreshLocationSilently() {
        // This is ONLY called when we know permission is already granted
        navigator.geolocation.getCurrentPosition(position => {
            dispatchLocationEvent(position.coords.latitude, position.coords.longitude, false);
        }, err => console.warn("Silent refresh failed", err));
    }

    function dispatchLocationEvent(lat, lon, isCached) {
        const locData = { lat, lon, timestamp: new Date().getTime() };
        localStorage.setItem('synocast_cached_location', JSON.stringify(locData));
        localStorage.setItem('synocast_permission_hint', 'true');
        sessionStorage.setItem('synocast_location_fixed', 'true');
        
        window.synocast_current_loc = { lat, lon, isCached };

        window.dispatchEvent(new CustomEvent('synocast_location_granted', {
            detail: window.synocast_current_loc
        }));

        // Store in IndexedDB for offline access
        if (typeof offlineStorage !== 'undefined') {
            offlineStorage.setSetting('lastLocation', { lat, lon, timestamp: Date.now() });
        }

        // Start location monitoring if enabled
        if (autoUpdateEnabled && !isCached) {
            startLocationMonitoring();
        }
    }

    /**
     * Start monitoring location changes
     */
    function startLocationMonitoring() {
        if (!navigator.geolocation || locationWatchId) return;

        console.log('[Location] Starting location monitoring...');

        const options = {
            enableHighAccuracy: false, // Use network-based location for battery efficiency
            timeout: 30000,
            maximumAge: 60000 // Accept cached positions up to 1 minute old
        };

        locationWatchId = navigator.geolocation.watchPosition(
            handleLocationUpdate,
            (error) => {
                console.warn('[Location] Watch position error:', error.message);
            },
            options
        );
    }

    /**
     * Stop monitoring location changes
     */
    function stopLocationMonitoring() {
        if (locationWatchId) {
            navigator.geolocation.clearWatch(locationWatchId);
            locationWatchId = null;
            console.log('[Location] Stopped location monitoring');
        }
    }

    /**
     * Handle location updates from watchPosition
     */
    function handleLocationUpdate(position) {
        const newLat = position.coords.latitude;
        const newLon = position.coords.longitude;

        if (!window.synocast_current_loc) return;

        const oldLat = window.synocast_current_loc.lat;
        const oldLon = window.synocast_current_loc.lon;

        // Calculate distance moved
        const distanceKm = calculateDistance(oldLat, oldLon, newLat, newLon);

        console.log(`[Location] Distance moved: ${distanceKm.toFixed(2)} km`);

        // Check if we should update
        if (distanceKm >= LOCATION_UPDATE_THRESHOLD_KM) {
            const now = Date.now();
            
            // Debounce updates
            if (now - lastUpdateTime < UPDATE_DEBOUNCE_MS) {
                console.log('[Location] Update debounced');
                return;
            }

            lastUpdateTime = now;
            console.log('[Location] Significant location change detected, updating...');

            // Update location
            dispatchLocationEvent(newLat, newLon, false);

            // Trigger weather refresh
            window.dispatchEvent(new CustomEvent('synocast_location_changed', {
                detail: {
                    lat: newLat,
                    lon: newLon,
                    distanceMoved: distanceKm
                }
            }));

            // Show notification to user
            if (typeof ToastUtils !== 'undefined') {
                ToastUtils.show(
                    'Location Updated',
                    `You've moved ${distanceKm.toFixed(1)} km. Refreshing weather data...`,
                    'info'
                );
            }
        }
    }

    /**
     * Calculate distance between two coordinates using Haversine formula
     * @returns distance in kilometers
     */
    function calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in km
        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);
        
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = R * c;
        
        return distance;
    }

    function toRad(degrees) {
        return degrees * (Math.PI / 180);
    }

    function handleLocationGranted(position) {
        // This is called after a USER ACTION (clicking enable in our modal)
        dispatchLocationEvent(position.coords.latitude, position.coords.longitude, false);
    }

    const enableBtn = document.getElementById('btn-enable-location');
    const searchBtn = document.getElementById('btn-search-manually');

    if (enableBtn) {
        enableBtn.onclick = () => {
            modal.hide();
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    handleLocationGranted(position);
                },
                (error) => {
                    console.warn("Location access denied:", error);
                    ToastUtils.show("Location Required", "Weather updates require location access. Please enable it in browser settings.", "error");
                    modal.show();
                }
            );
        };
    }

    if (searchBtn) {
        searchBtn.onclick = () => {
            modal.hide();
            if (window.location.pathname !== '/') {
                window.location.href = '/?focusSearch=true';
            } else {
                const searchInput = document.getElementById('new-city-input');
                if (searchInput) {
                    setTimeout(() => searchInput.focus(), 500);
                }
            }
        };
    }

    // Expose functions for external control
    window.SynocastLocation = {
        startMonitoring: startLocationMonitoring,
        stopMonitoring: stopLocationMonitoring,
        setAutoUpdate: (enabled) => {
            autoUpdateEnabled = enabled;
            if (enabled) {
                startLocationMonitoring();
            } else {
                stopLocationMonitoring();
            }
        },
        isMonitoring: () => locationWatchId !== null
    };
});
