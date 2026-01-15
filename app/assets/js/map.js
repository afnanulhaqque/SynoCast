// Global Map Explorer Logic

let map;
let weatherOverlay = null;

// Default to a central view (London) if geolocation fails
const defaultLat = 51.505;
const defaultLon = -0.09;
const defaultZoom = 3;

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initSearch();
    
    // Auto-locate implementation
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                // Fly to user location with a closer zoom
                if (map) {
                    map.flyTo([latitude, longitude], 10, {
                        animate: true,
                        duration: 1.5
                    });
                    
                    // Show a marker
                    L.marker([latitude, longitude]).addTo(map);
                     
                     // Fetch weather and show popup immediately
                     fetchMapWeather(latitude, longitude, "Your Location", true);
                }
            },
            (error) => {
                console.warn("Geolocation denied or failed:", error.message);
                // Optional: Show a toast/alert saying "Location access denied, showing global view"
            }
        );
    }
});

function initMap() {
    // 1. Initialize Leaflet
    map = L.map('weather-map', {
        center: [defaultLat, defaultLon],
        zoom: defaultZoom,
        maxZoom: 18,
        minZoom: 2,
        worldCopyJump: true,
        zoomControl: false // Disable default top-left
    });

    // Add Zoom Control to Bottom Right
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // 2. Base Layer
    const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // 3. Weather Overlays (Clouds & Precip by default)
    // "Remove overlay" request: We will just add the layers directly but NOT the control widget.
    const clouds = L.tileLayer('/api/proxy/tiles/clouds_new/{z}/{x}/{y}', { maxZoom: 18, opacity: 0.8 }).addTo(map);
    const precip = L.tileLayer('/api/proxy/tiles/precipitation_new/{z}/{x}/{y}', { maxZoom: 18, opacity: 0.7 }).addTo(map);
    
    // We keep the layers active but remove the UI control as requested ("overlay khatam kro")
    // If the user meant something else, they can clarify, but this removes the box.

    // 5. Click to Inspect
    map.on('click', async (e) => {
        const { lat, lng } = e.latlng;
        // Show loading state in panel or popup?
        // Let's us a popup first
        L.popup()
            .setLatLng(e.latlng)
            .setContent('<div class="text-center p-2"><div class="spinner-border spinner-border-sm text-primary"></div></div>')
            .openOn(map);
            
        await fetchMapWeather(lat, lng, null, true); // true = update popup
    });
}

async function fetchMapWeather(lat, lon, cityNameOverride = null, updatePopup = false) {
    const panel = document.getElementById('map-info-panel');
    const panelCity = document.getElementById('map-city');
    const panelTemp = document.getElementById('map-temp');
    const panelCondition = document.getElementById('map-condition');
    const panelIcon = document.getElementById('map-icon');
    const panelWind = document.getElementById('map-wind');
    const panelHum = document.getElementById('map-humidity');
    const panelPress = document.getElementById('map-pressure');
    const closeBtn = document.getElementById('close-map-info');
    
    // Close handler
    if (closeBtn) {
        closeBtn.onclick = () => {
            panel.style.display = 'none';
        }
    }

    try {
        const res = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
        const data = await res.json();
        const current = data.current;
        
        const name = cityNameOverride || current.name || `Lat: ${lat.toFixed(2)}, Lon: ${lon.toFixed(2)}`;
        const tempVal = Math.round(current.main.temp);
        const condition = current.weather[0].description;
        const iconCode = current.weather[0].icon;
        const weatherId = current.weather[0].id;
        
        // Use styled icons via WeatherUtils
        const iconData = WeatherUtils.getIconClass(weatherId, iconCode);

        // Update Panel
        if (panelCity) panelCity.textContent = name;
        if (panelTemp) panelTemp.textContent = `${tempVal}°C`;
        if (panelCondition) panelCondition.textContent = condition; // Capitalize?
        
        if (panelIcon) {
            // It's now an <i> tag
            panelIcon.className = `fas ${iconData.icon} fa-2x ${iconData.animation} ${iconData.color}`;
        }
        
        if (panelWind) panelWind.textContent = `${Math.round(current.wind.speed * 3.6)} km/h`;
        if (panelHum) panelHum.textContent = `${current.main.humidity}%`;
        if (panelPress) panelPress.textContent = `${current.main.pressure} hPa`;
        
        // Show Panel
        panel.style.display = 'block';
        
        // Update Popup if requested
        if (updatePopup && map) {
            const popupContent = `
                <div class="weather-popup-card">
                    <h6 class="fw-bold mb-1 text-truncate" style="max-width: 100%;">${name}</h6>
                    <div class="py-2">
                        <i class="fas ${iconData.icon} fa-3x ${iconData.animation} ${iconData.color}"></i>
                    </div>
                    <div class="d-flex justify-content-center align-items-center gap-2">
                        <span class="fw-bold fs-4 text-dark">${tempVal}°</span>
                    </div>
                    <div class="small text-muted text-capitalize mt-1">${condition}</div>
                </div>
            `;
            // Retrieve the currently open popup (hacky but works for single click)
            map.closePopup(); // Close loading popup
            L.popup()
                .setLatLng([lat, lon])
                .setContent(popupContent)
                .openOn(map);
        }

    } catch (err) {
        console.error("Map click weather fetch failed", err);
    }
}

// --- Search Logic ---
function initSearch() {
    const input = document.getElementById('map-search-input');
    const btn = document.getElementById('map-search-btn');
    const list = document.getElementById('map-search-results');
    
    if (!input) return;

    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const query = input.value.trim();
        
        if (query.length < 2) {
            list.innerHTML = '';
            list.classList.remove('show');
            list.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/weather/autocomplete?q=${encodeURIComponent(query)}`);
                const suggestions = await res.json();
                
                list.innerHTML = '';
                if (suggestions.length > 0) {
                    list.classList.add('show');
                    list.style.display = 'block';
                    suggestions.forEach(city => {
                        const item = document.createElement('li');
                        item.className = 'dropdown-item cursor-pointer';
                        item.innerHTML = `<i class="fas fa-map-marker-alt text-muted me-2"></i> ${city.name}, <small class="text-muted">${city.country}</small>`;
                        item.onclick = () => {
                            input.value = `${city.name}, ${city.country}`;
                            list.classList.remove('show');
                            // Fly to location
                            if (map) {
                                map.flyTo([city.lat, city.lon], 10, { duration: 1.5 });
                                fetchMapWeather(city.lat, city.lon, city.name, true);
                            }
                        };
                        list.appendChild(item);
                    });
                } else {
                    list.classList.remove('show');
                    list.style.display = 'none';
                }
            } catch (err) {
                console.error("Search failed", err);
            }
        }, 300);
    });

    // Hide list on click outside
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !list.contains(e.target)) {
            list.classList.remove('show');
        }
    });
    
    if(btn) {
        btn.onclick = () => {
            // Trigger first result if available? or just focus
            input.focus();
        }
    }
}
