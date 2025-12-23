/**
 * Universal Location Handler for SynoCast
 * This script handles checking for location permissions and showing the custom modal
 * across all pages of the application.
 */

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

        if (cachedLoc && (now - cachedLoc.timestamp < 3600000)) {
            window.synocast_current_loc = { lat: cachedLoc.lat, lon: cachedLoc.lon, isCached: true };
            setTimeout(() => {
                window.dispatchEvent(new CustomEvent('synocast_location_granted', {
                    detail: window.synocast_current_loc
                }));
            }, 100);
        }

        // Use Permissions API to check without prompting
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const result = await navigator.permissions.query({ name: 'geolocation' });
                if (result.state === 'granted') {
                    // Permission already granted, we can call getCurrentPosition WITHOUT a browser prompt
                    refreshLocationSilently();
                } else if (result.state === 'prompt') {
                    // This is where we show ONLY our custom modal. We DON'T call getCurrentPosition here.
                    if (!cachedLoc || (now - cachedLoc.timestamp >= 3600000)) {
                        setTimeout(() => {
                            if (!window.synocast_current_loc) modal.show();
                        }, 1500);
                    }
                }

                result.onchange = function () {
                    if (this.state === 'granted') {
                        modal.hide();
                        refreshLocationSilently();
                    }
                };
            } catch (e) {
                if (!window.synocast_current_loc) setTimeout(() => modal.show(), 2000);
            }
        } else {
            // Browsers like older Safari (no query support) - still show our modal first
            if (!window.synocast_current_loc) setTimeout(() => modal.show(), 2000);
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
        sessionStorage.setItem('synocast_location_fixed', 'true');
        
        window.synocast_current_loc = { lat, lon, isCached };

        window.dispatchEvent(new CustomEvent('synocast_location_granted', {
            detail: window.synocast_current_loc
        }));
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
                    alert("Location access is required for full functionality. Please enable it in browser settings.");
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
});
