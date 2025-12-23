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

    async function checkLocationStatus() {
        if (!navigator.geolocation) return;

        // Use Permissions API to check without prompting
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const result = await navigator.permissions.query({ name: 'geolocation' });
                if (result.state === 'granted') {
                    // Already have it, no need for popup
                    handleLocationGranted();
                } else {
                    // State is 'prompt' or 'denied'
                    modal.show();
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
                modal.show();
            }
        } else {
            // Browsers like Safari might not support permissions.query
            modal.show();
        }
    }

    function handleLocationGranted() {
        navigator.geolocation.getCurrentPosition(position => {
            sessionStorage.setItem('synocast_location_fixed', 'true');
            // Notify other scripts (like home_weather_card.js) that location is available
            window.dispatchEvent(new CustomEvent('synocast_location_granted', {
                detail: {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
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
            // If we are not on home, redirect to home to search? 
            // Or just allow them to dismiss. 
            // For now, let's keep it simple.
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

    // Check on load
    if (!hasLocation) {
        // Shorter delay to show popup on all pages
        setTimeout(checkLocationStatus, 1500);
    }
});
