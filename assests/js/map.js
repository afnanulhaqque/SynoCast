document.addEventListener('DOMContentLoaded', function() {
    // --- Map Initialization ---
    const map = L.map('map').setView([51.505, -0.09], 5); // Default to London, Zoomed out

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Add a marker to the map
    let marker = L.marker([51.505, -0.09]).addTo(map);

    // Try to get user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            map.setView([lat, lon], 16);
            marker.setLatLng([lat, lon]); // Update marker position
            updateWeather(lat, lon);
        }, () => {
            // Fallback if permission denied or error
            updateWeather(51.505, -0.09);
        });
    } else {
        updateWeather(51.505, -0.09);
    }

    // Update weather on map move
    map.on('moveend', function() {
        const center = map.getCenter();
        marker.setLatLng(center); // Move marker to center
        updateWeather(center.lat, center.lng);
    });

    // --- Map Controls ---

    // Search Functionality
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('location-search');

    async function searchLocation() {
        const query = searchInput.value;
        if (!query) return;

        const url = `/api/geocode/search?q=${encodeURIComponent(query)}`;

        try {
            const res = await fetch(url);
            const data = await res.json();

            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                map.setView([lat, lon], 16); // Zoom in on result
                marker.setLatLng([lat, lon]);
                updateWeather(lat, lon);
            } else {
                alert('Location not found');
            }
        } catch (error) {
            console.error("Search error:", error);
            alert('Error searching for location');
        }
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', searchLocation);
    }
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchLocation();
        }
    });

    // Locate Me Functionality
    document.getElementById('locate-btn').addEventListener('click', function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                map.setView([lat, lon], 16);
                marker.setLatLng([lat, lon]);
                updateWeather(lat, lon);
            }, () => {
                alert('Unable to retrieve your location');
            });
        } else {
            alert('Geolocation is not supported by your browser');
        }
    });


    async function updateWeather(lat, lon) {
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m`;
        const geocodeUrl = `/api/geocode/reverse?lat=${lat}&lon=${lon}`;

        // Show loading state
        document.getElementById('weather-city').textContent = "Loading...";

        try {
            // Fetch Weather
            const weatherRes = await fetch(weatherUrl);
            const weatherData = await weatherRes.json();

            // Fetch City Name (Reverse Geocoding)
            const geoRes = await fetch(geocodeUrl);
            const geoData = await geoRes.json();

            // Update UI
            if (weatherData.current) {
                document.getElementById('weather-temp').textContent = Math.round(weatherData.current.temperature_2m);
                document.getElementById('weather-wind').textContent = `${weatherData.current.wind_speed_10m} km/h`;
                document.getElementById('weather-humidity').textContent = `${weatherData.current.relative_humidity_2m}%`;
            }

            let locationName = "Unknown Location";
            if (geoData.address) {
                locationName = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.county || "Unknown Location";
            }
            document.getElementById('weather-city').textContent = locationName;

        } catch (error) {
            console.error("Error fetching data:", error);
            document.getElementById('weather-city').textContent = "Error loading data";
        }
    }
});
