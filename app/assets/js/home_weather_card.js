document.addEventListener('DOMContentLoaded', function() {
    const favoritesList = document.getElementById('favorites-list');
    const newCityInput = document.getElementById('new-city-input');
    const addCityBtn = document.getElementById('add-city-btn');
    
    // UI Elements
    const cityEl = document.getElementById('home-city-name');
    const tempEl = document.getElementById('home-temp');
    const windEl = document.getElementById('home-wind');
    const humidityEl = document.getElementById('home-humidity');
    const timeEl = document.getElementById('home-time');
    const dateEl = document.getElementById('home-date');
    const dayEl = document.getElementById('home-day');
    const forecastEl = document.getElementById('home-hourly-forecast');

    // Load favorites
    let favorites = JSON.parse(localStorage.getItem('weatherFavorites')) || [];

    function renderFavorites() {
        favoritesList.innerHTML = '';
        if (favorites.length === 0) {
            favoritesList.innerHTML = '<li><span class="dropdown-item text-muted">No favorites added</span></li>';
        } else {
            favorites.forEach(city => {
                const li = document.createElement('li');
                li.className = 'd-flex justify-content-between align-items-center px-3 py-1';
                
                const span = document.createElement('span');
                span.className = 'dropdown-item p-0 text-truncate';
                span.style.cursor = 'pointer';
                span.style.maxWidth = '180px';
                span.textContent = city.name;
                
                // Click to select city
                span.onclick = () => {
                    fetchWeather(city.lat, city.lon, city.name);
                };
                
                const removeBtn = document.createElement('i');
                removeBtn.className = 'fa-solid fa-trash text-danger ms-2';
                removeBtn.style.cursor = 'pointer';
                removeBtn.style.fontSize = '0.8rem';
                removeBtn.onclick = (e) => {
                    e.stopPropagation(); // Prevent triggering selection
                    removeFavorite(city.name);
                };

                li.appendChild(span);
                li.appendChild(removeBtn);
                favoritesList.appendChild(li);
            });
        }
    }

    function removeFavorite(name) {
        favorites = favorites.filter(c => c.name !== name);
        localStorage.setItem('weatherFavorites', JSON.stringify(favorites));
        renderFavorites();
    }

    if (newCityInput) {
        const newCityResults = document.getElementById('new-city-results');
        AutocompleteUtils.initAutocomplete(newCityInput, newCityResults, (city) => {
            // Check if already exists
            if (!favorites.some(f => f.name === city.name)) {
                favorites.push(city);
                localStorage.setItem('weatherFavorites', JSON.stringify(favorites));
                renderFavorites();
                newCityInput.value = '';
            } else {
                ToastUtils.show("Favorites", "City already in your favorites list.", "warning");
            }
        });

        // Prevent dropdown from closing when clicking input
        newCityInput.addEventListener('click', (e) => e.stopPropagation());
    }

    async function fetchWeather(lat, lon, cityName, silent = false) {
        if(cityEl && !silent) cityEl.textContent = cityName || "Loading...";
        
        const weatherUrl = `/api/weather?lat=${lat}&lon=${lon}`;
        
        try {
            const res = await fetch(weatherUrl);
            const data = await res.json();
            
            if (data.current) {
                // Save to cache
                data.cityName = cityName;
                localStorage.setItem('synocast_weather_cache', JSON.stringify(data));

                // Current Weather Data Mapping (OpenWeatherMap)
                if(tempEl) tempEl.textContent = `${Math.round(data.current.main.temp)}°`;
                if(windEl) windEl.textContent = WeatherUtils.formatWind(data.current.wind.speed); // Use shared formatter
                if(humidityEl) humidityEl.textContent = `${data.current.main.humidity}%`;
                
                // Update time/date
                const offsetSeconds = data.current.timezone; 
                const localTime = new Date(new Date().getTime() + (offsetSeconds * 1000) + (new Date().getTimezoneOffset() * 60000));

                if(timeEl) timeEl.textContent = localTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
                if(dateEl) dateEl.textContent = localTime.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
                if(dayEl) dayEl.textContent = "Today"; 
                
                if (data.current.weather && data.current.weather[0]) {
                     const conditionEl = document.getElementById('home-condition');
                     if(conditionEl) conditionEl.textContent = data.current.weather[0].main;
                }
            }

            if (data.forecast && forecastEl) {
                updateForecast(data.forecast, data.current.timezone);
            }

        } catch (error) {
            if(!silent) {
                if(cityEl) cityEl.textContent = "Error";
                showLocationPrompt();
            }
        }
    }

    function updateForecast(forecastData, timezoneOffset) {
        if(!forecastEl) return;
        forecastEl.innerHTML = '';
        const hourlyList = forecastData.list;
        for (let i = 0; i < 5; i++) {
            if (i >= hourlyList.length) break;
            const item = hourlyList[i];
            const temp = Math.round(item.main.temp);
            const date = new Date(item.dt * 1000);
            const itemTime = new Date(date.getTime() + (timezoneOffset * 1000) + (date.getTimezoneOffset() * 60000));
            const timeStr = itemTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
            const wCode = item.weather[0].id;
            const iconClass = WeatherUtils.getIconClass(wCode, item.weather[0].icon);
            const div = document.createElement('div');
            div.className = i === 0 ? 'bg-primary text-white rounded-3 py-4 d-flex flex-column align-items-center justify-content-center forecast-card-hover' : 'bg-light text-primary rounded-3 py-4 d-flex flex-column align-items-center justify-content-center forecast-card-hover';
            div.style.minWidth = '55px';
            div.innerHTML = `
                <p class="small mb-1" style="font-size: 10px;">${timeStr}</p>
                <i class="fa-solid ${iconClass} mb-1"></i>
                <p class="small mb-0 fw-bold">${temp}°</p>
            `;
            forecastEl.appendChild(div);
        }
    }

    function showLocationPrompt() {
        if(cityEl) cityEl.textContent = "Turn on your location";
        if(tempEl) tempEl.textContent = "--";
        if(windEl) windEl.textContent = "--";
        if(humidityEl) humidityEl.textContent = "--";
        const aqiEl = document.getElementById('home-aqi');
        if(aqiEl) aqiEl.textContent = "--";
        
        // Use current system time
        const now = new Date();
        if(timeEl) timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        if(dateEl) dateEl.textContent = now.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
        if(dayEl) dayEl.textContent = "Today";
        
        // Clear specific elements
        const conditionEl = document.getElementById('home-condition');
        if(conditionEl) conditionEl.textContent = "";
        
        if(forecastEl) {
             forecastEl.innerHTML = `
                <div class="d-flex flex-column align-items-center justify-content-center w-100 text-muted py-3">
                    <span class="material-icons mb-2" style="font-size: 2rem; opacity: 0.5;">&#xe0c7;</span>
                    <small>Location access needed</small>
                </div>
             `;
        }
    }

    function getCurrentLocation() {
        // This is now mostly handled by location_handler.js
        // If we already have permission, location_handler will fire the event.
        // If not, it will show the modal.
        
        // However, we still need to set the initial "Turn on your location" state on the card
        showLocationPrompt();
    }

    // Listen for global location grant
    window.addEventListener('synocast_location_granted', async (e) => {
        handleLocationEvent(e.detail);
    });

    // Immediate check
    if (window.synocast_current_loc) {
        handleLocationEvent(window.synocast_current_loc);
    }

    async function handleLocationEvent(detail) {
        const { lat, lon, isCached } = detail;
        
        // Show cached weather if available
        const cachedWeather = JSON.parse(localStorage.getItem('synocast_weather_cache'));
        if (cachedWeather && isCached) {
            renderWeatherData(cachedWeather);
        }

        // Silent refresh in background
        const geoUrl = `/api/geocode/reverse?lat=${lat}&lon=${lon}`;
        try {
            const res = await fetch(geoUrl);
            const data = await res.json();
            const name = data.address.city || data.address.town || data.address.village || "My Location";
            fetchWeather(lat, lon, name, !!isCached);
        } catch (e) {
            fetchWeather(lat, lon, "My Location", !!isCached);
        }
    }

    function renderWeatherData(data) {
        if (!data.current) return;
        if(tempEl) tempEl.textContent = `${Math.round(data.current.main.temp)}°`;
        if(windEl) windEl.textContent = WeatherUtils.formatWind(data.current.wind.speed);
        if(humidityEl) humidityEl.textContent = `${data.current.main.humidity}%`;
        if(cityEl) cityEl.textContent = data.cityName || data.current.name;
        
        if (data.current.weather && data.current.weather[0]) {
            const conditionEl = document.getElementById('home-condition');
            if(conditionEl) conditionEl.textContent = data.current.weather[0].main;
        }
        
        // Update weather scene image based on temperature
        const imgEl = document.getElementById('home-weather-img');
        if (imgEl) {
            const temp = data.current.main.temp;
            const weatherId = data.current.weather[0].id; // Use ID for better accuracy
            const main = data.current.weather[0].main.toLowerCase();
            
            // Map Weather Condition to Image
            const imgName = WeatherUtils.getWeatherSceneImage(weatherId);
            
            imgEl.src = `/assets/images/${imgName}`;
            imgEl.alt = data.current.weather[0].main; 
        }

        if (data.forecast && forecastEl) {
            updateForecast(data.forecast, data.current.timezone);
        }
    }

    // Handle manual search focus from other pages
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('focusSearch') === 'true') {
        setTimeout(() => {
            if (newCityInput) newCityInput.focus();
        }, 800);
    }

    // Initialize
    renderFavorites();
    
    // Check for cached weather on load
    const initialCache = JSON.parse(localStorage.getItem('synocast_weather_cache'));
    if (initialCache) {
        renderWeatherData(initialCache);
    } else {
        // IMPROVEMENT: Check top bar for initial location data (from IP-detection on server)
        const timeDisplay = document.getElementById('dynamic_time_display');
        const topCity = timeDisplay?.getAttribute('data-city');
        const topOffset = timeDisplay?.getAttribute('data-offset');
        
        if (topCity && topCity !== 'Unknown') {
            // We have a city from server-side IP detection
            // We need lat/lon to fetch weather. Since we don't have them yet, 
            // we can either geocode the city or rely on the IP fallback below.
            // But let's at least show the city name immediately.
            if(cityEl) cityEl.textContent = topCity;
            showLocationPrompt(); // Still show prompt but with city name
        } else {
            showLocationPrompt();
        }
    }
    
    // No explicit initialization needed here as location_handler.js
    // handles the synocast_location_granted event.
});
