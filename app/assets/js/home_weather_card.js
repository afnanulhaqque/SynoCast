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
    let favorites = [];

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
        renderFavorites();
    }

    if (newCityInput) {
        const newCityResults = document.getElementById('new-city-results');
        AutocompleteUtils.initAutocomplete(newCityInput, newCityResults, (city) => {
            // Check if already exists
            if (!favorites.some(f => f.name === city.name)) {
                favorites.push(city);
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
                    data.cityName = cityName;

                    // Helper to remove skeleton
                    const removeSkeleton = (el) => {
                        if (el) {
                            el.classList.remove('skeleton');
                            el.style.minWidth = '';
                            el.style.minHeight = '';
                        }
                    };

                    // Current Weather Data Mapping (OpenWeatherMap)
                    if(tempEl) { tempEl.textContent = `${Math.round(data.current.main.temp)}°`; removeSkeleton(tempEl); }
                    if(windEl) { windEl.textContent = WeatherUtils.formatWind(data.current.wind.speed); removeSkeleton(windEl); }
                    if(humidityEl) { humidityEl.textContent = `${data.current.main.humidity}%`; removeSkeleton(humidityEl); }
                    
                    // Update time/date
                    const offsetSeconds = data.current.timezone; 
                    const localTime = new Date(new Date().getTime() + (offsetSeconds * 1000) + (new Date().getTimezoneOffset() * 60000));

                    if(timeEl) { 
                        timeEl.textContent = localTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
                        removeSkeleton(timeEl);
                    }
                    if(dateEl) dateEl.textContent = localTime.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
                    if(dayEl) dayEl.textContent = "Today"; 
                    
                    // City Name
                    if(cityEl) { removeSkeleton(cityEl); } // Text is set at start of fetch, but remove skeleton now

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
        // Limit to 4 items to fit the narrow container (w-350) with margins
        for (let i = 0; i < 4; i++) {
            if (i >= hourlyList.length) break;
            const item = hourlyList[i];
            const temp = Math.round(item.main.temp);
            const date = new Date(item.dt * 1000);
            const itemTime = new Date(date.getTime() + (timezoneOffset * 1000) + (date.getTimezoneOffset() * 60000));
            const timeStr = itemTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
            const wCode = item.weather[0].id;
            const iconData = WeatherUtils.getIconClass(wCode, item.weather[0].icon);
            const div = document.createElement('div');
            // Use 'active-forecast-pill' class for the first item for easier styling
            const isActive = (i === 0);
            div.className = isActive 
                ? 'active-forecast-pill d-flex flex-column align-items-center justify-content-center py-3 px-2 shadow-sm' 
                : 'forecast-pill d-flex flex-column align-items-center justify-content-center py-3 px-2';
            
            div.style.minWidth = '60px'; // Slightly wider
            div.style.borderRadius = '50px'; // Pill shape
            div.style.transition = 'transform 0.2s';
            div.style.cursor = 'pointer';

            // Inline styles for colors to ensure they stick regardless of CSS specificity issues
            const bgColor = isActive ? 'var(--primary-color)' : '#f8f9fa';
            const textColor = isActive ? '#ffffff' : 'var(--text-primary)';
            
            div.style.background = bgColor;
            div.style.color = textColor;

            div.innerHTML = `
                <p class="mb-2" style="font-size: 0.75rem; font-weight: 500; margin: 0;">${timeStr}</p>
                <i class="fa-solid ${iconData.icon} mb-2" style="font-size: 1.2rem;"></i>
                <p class="mb-0 fw-bold" style="font-size: 1rem;">${temp}°</p>
            `;
            
            // Add hover effect via JS events since we are using inline styles
            div.onmouseenter = () => { div.style.transform = 'translateY(-5px)'; };
            div.onmouseleave = () => { div.style.transform = 'translateY(0)'; };

            forecastEl.appendChild(div);
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


        
        
        // Update weather icon (Large)
        const iconContainer = document.getElementById('home-weather-icon-container');
        if (iconContainer && data.current.weather && data.current.weather[0]) {
            const weatherId = data.current.weather[0].id;
            const iconCode = data.current.weather[0].icon;
            
            // Get proper icon class
            const weatherMeta = WeatherUtils.getIconClass(weatherId, iconCode);
            
            // Create vibrant icon
            iconContainer.innerHTML = `
                <i class="fa-solid ${weatherMeta.icon} text-primary" 
                   style="font-size: 7rem; filter: drop-shadow(0 10px 20px rgba(58, 91, 160, 0.3)); 
                          animation: float 6s ease-in-out infinite;"></i>
            `;
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
    
    // Check top city on load
    const timeDisplay = document.getElementById('dynamic_time_display');
    const topCity = timeDisplay?.getAttribute('data-city');
    
    if (topCity && topCity !== 'Unknown') {
        if(cityEl) cityEl.textContent = topCity;
        showLocationPrompt(); 
    } else {
        showLocationPrompt();
    }
});
