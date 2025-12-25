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
});
