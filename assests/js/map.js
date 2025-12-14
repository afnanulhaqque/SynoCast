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
        const weatherUrl = `/api/weather?lat=${lat}&lon=${lon}`;
        const geocodeUrl = `/api/geocode/reverse?lat=${lat}&lon=${lon}`;

        // Show loading state
        document.getElementById('weather-city').textContent = "Loading...";

        try {
            // Fetch Weather
            const weatherRes = await fetch(weatherUrl);
            const weatherData = await weatherRes.json();

            // Fetch City Name (Reverse Geocoding)
            // We can still use this for better location details if OWM name is too generic
            const geoRes = await fetch(geocodeUrl);
            const geoData = await geoRes.json();

            // Update UI
            if (weatherData.current) {
                // OpenWeatherMap returns temp in Celsius (metric units requested in backend)
                document.getElementById('weather-temp').textContent = Math.round(weatherData.current.main.temp);
                document.getElementById('weather-wind').textContent = `${weatherData.current.wind.speed} m/s`;
                document.getElementById('weather-humidity').textContent = `${weatherData.current.main.humidity}%`;
                
                // Update Icon
                const w = weatherData.current.weather[0];
                const id = w.id;
                let iconClass = 'fa-sun';
                if (id >= 200 && id < 300) iconClass = 'fa-bolt';
                else if (id >= 300 && id < 500) iconClass = 'fa-cloud-rain';
                else if (id >= 500 && id < 600) iconClass = 'fa-cloud-showers-heavy';
                else if (id >= 600 && id < 700) iconClass = 'fa-snowflake';
                else if (id >= 700 && id < 800) iconClass = 'fa-smog';
                else if (id === 800) iconClass = w.icon.includes('n') ? 'fa-moon' : 'fa-sun';
                else if (id > 800) iconClass = 'fa-cloud';

                const iconContainer = document.getElementById('weather-icon');
                if (iconContainer) {
                    iconContainer.innerHTML = `<i class="fas ${iconClass} fa-2x"></i>`;
                }
            }

            let locationName = "Unknown Location";
            if (geoData.address) {
                locationName = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.county || "Unknown Location";
            } else if (weatherData.current && weatherData.current.name) {
                 locationName = weatherData.current.name;
            }
            document.getElementById('weather-city').textContent = locationName;

        } catch (error) {
            console.error("Error fetching data:", error);
            document.getElementById('weather-city').textContent = "Error loading data";
        }
    }
});
