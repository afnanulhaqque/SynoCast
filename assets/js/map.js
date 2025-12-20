document.addEventListener('DOMContentLoaded', function() {
    // --- Map Initialization ---
    // --- Map Initialization ---
    
    // 1. Define Base Layers
    const standardLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    });

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    });

    const satelliteLabels = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        attribution: ''
    });

    // Group Satellite + Labels
    const satelliteHybrid = L.layerGroup([satelliteLayer, satelliteLabels]);

    // 2. Initialize Map with Default Layer
    const map = L.map('map', {
        center: [51.505, -0.09],
        zoom: 5,
        layers: [satelliteHybrid], // Default to Satellite as requested last
        attributionControl: false // Remove attribution as requested
    });

    // 3. Add Layer Control
    const baseMaps = {
        "Standard": standardLayer,
        "Satellite": satelliteHybrid
    };

    const layerControl = L.control.layers(baseMaps, null, { position: 'bottomleft' });
    
    // Override _initLayout to prevent default behavior completely
    const originalInitLayout = layerControl._initLayout;
    layerControl._initLayout = function() {
        originalInitLayout.call(this);
        // Remove standard Leaflet listeners
        L.DomEvent.off(this._container, 'mouseenter', this.expand, this);
        L.DomEvent.off(this._container, 'mouseleave', this.collapse, this);
    };

    layerControl.addTo(map);

    const container = layerControl.getContainer();
    
    // Prevent map interactions
    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.disableScrollPropagation(container);

    // 1. OPEN ON HOVER
    container.addEventListener('mouseenter', function() {
        layerControl.expand();
    });

    // 2. CLOSE ON CLICK (Toggle logic)
    // If we click while expanded, it should collapse.
    // If we click while collapsed (and somehow didn't hover? e.g. touch), it expands.
    container.addEventListener('click', function(e) {
        // If clicking an input/label, let it do its job (change layer) but don't collapse immediately? 
        // Or maybe user wants to click icon to close?
        // Standard Leaflet hides the icon when expanded. So clicking "the icon" when expanded is impossible unless we style it differently.
        // But if user clicks the *header* or *container*, we can toggle.
        
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'LABEL' || e.target.tagName === 'SPAN') {
            return; 
        }

        if (container.classList.contains('leaflet-control-layers-expanded')) {
            layerControl.collapse();
        } else {
            layerControl.expand();
        }
    });

    // Close when clicking map
    map.on('click', function() {
        layerControl.collapse();
    });

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
        const overlay = document.getElementById('weather-overlay');
        if (overlay) overlay.classList.add('loading');
        
        const mapCityEl = document.getElementById('map-city');
        if (mapCityEl) mapCityEl.textContent = "Loading...";

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
                const mapTempEl = document.getElementById('map-temp');
                if (mapTempEl) mapTempEl.textContent = Math.round(weatherData.current.main.temp);
                
                const mapWindEl = document.getElementById('map-wind');
                if (mapWindEl) mapWindEl.textContent = WeatherUtils.formatWind(weatherData.current.wind.speed);
                
                const mapHumEl = document.getElementById('map-humidity');
                if (mapHumEl) mapHumEl.textContent = `${weatherData.current.main.humidity}%`;
                
                // Update Icon
                const w = weatherData.current.weather[0];
                const iconClass = WeatherUtils.getIconClass(w.id, w.icon);

                const iconContainer = document.getElementById('map-icon');
                if (iconContainer) {
                    iconContainer.innerHTML = `<i class="fas ${iconClass}"></i>`;
                }
            }

            let locationName = "Unknown Location";
            if (geoData.address) {
                locationName = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.county || "Unknown Location";
            } else if (weatherData.current && weatherData.current.name) {
                 locationName = weatherData.current.name;
            }
            if (mapCityEl) mapCityEl.textContent = locationName;

        } catch (error) {
            const mapCityEl = document.getElementById('map-city');
            if (mapCityEl) mapCityEl.textContent = "Error loading data";
        } finally {
            if (overlay) overlay.classList.remove('loading');
        }
    }
});
