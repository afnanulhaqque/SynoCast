/**
 * Universal Location Handler for SynoCast
 * This script handles checking for location permissions and showing the custom modal
 * across all pages of the application.
 */

document.addEventListener('DOMContentLoaded', function () {
    // We only want to auto-trigger if we haven't successfully fetched location in this session
    // or if the user hasn't explicitly dismissed it for now.
    const hasLocation = sessionStorage.getItem('synocast_location_fixed');

    // Only run if the modal exists in the current page (it should be in base.html)
    const modalEl = document.getElementById('locationPermissionModal');
    if (!modalEl) return;

    const modal = new bootstrap.Modal(modalEl);

    // Check on load immediately
    checkLocationStatus();

    async function checkLocationStatus() {
        if (!navigator.geolocation) return;

        // Check for cached location (60 minutes = 3600000 ms)
        const cachedLoc = JSON.parse(localStorage.getItem('synocast_cached_location'));
        const now = new Date().getTime();

        if (cachedLoc && (now - cachedLoc.timestamp < 3600000)) {
            // Use cached location immediately (Instant load)
            window.dispatchEvent(new CustomEvent('synocast_location_granted', {
                detail: {
                    lat: cachedLoc.lat,
                    lon: cachedLoc.lon,
                    isCached: true
                }
            }));
            // We still continue to check/refresh in background
        }

        // Use Permissions API to check without prompting
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const result = await navigator.permissions.query({ name: 'geolocation' });
                if (result.state === 'granted') {
                    // Refresh location in background
                    handleLocationGranted();
                } else if (result.state === 'prompt') {
                    // State is 'prompt', show modal with a slight delay if no cached location
                    if (!cachedLoc || (now - cachedLoc.timestamp >= 3600000)) {
                        setTimeout(() => modal.show(), 1000);
                    }
                }

                // Listen for changes
                result.onchange = function () {
                    if (this.state === 'granted') {
                        modal.hide();
                        handleLocationGranted();
                    }
                };
            } catch (e) {
                // Fallback for browsers that don't support geolocation permission query
                if (!hasLocation) setTimeout(() => modal.show(), 1200);
            }
        } else {
            // Browsers like Safari might not support permissions.query
            if (!hasLocation) setTimeout(() => modal.show(), 1200);
        }
    } // This is the missing closing brace for checkLocationStatus

    function handleLocationGranted() {
        navigator.geolocation.getCurrentPosition(position => {
            const locData = {
                lat: position.coords.latitude,
                lon: position.coords.longitude,
                timestamp: new Date().getTime()
            };
            localStorage.setItem('synocast_cached_location', JSON.stringify(locData));
            sessionStorage.setItem('synocast_location_fixed', 'true');
            
            // Notify other scripts
            window.dispatchEvent(new CustomEvent('synocast_location_granted', {
                detail: {
                    lat: locData.lat,
                    lon: locData.lon
                }
            }));
        });
    }

    // Wire up the modal buttons
    const enableBtn = document.getElementById('btn-enable-location');
    const searchBtn = document.getElementById('btn-search-manually');

    if (enableBtn) {
        enableBtn.onclick = () => {
            modal.hide();
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    handleLocationGranted();
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
