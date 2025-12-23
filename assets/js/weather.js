
document.addEventListener('DOMContentLoaded', function() {
    // --- State Variables ---
    let currentData = null;
    let forecastData = null;
    let currentUnit = 'C'; 

    // --- UI Elements ---
    const cityEl = document.getElementById('weather-city');
    const countryEl = document.getElementById('weather-country');
    const dateHeaderEl = document.getElementById('weather-date-header');
    
    const heroTempEl = document.getElementById('weather-hero-temp');
    const heroIconEl = document.getElementById('weather-hero-icon');
    const heroConditionEl = document.getElementById('weather-hero-condition');
    
    const maxTempEl = document.getElementById('weather-max-temp');
    const minTempEl = document.getElementById('weather-min-temp');
    const windEl = document.getElementById('weather-hero-wind');
    const humidityEl = document.getElementById('weather-hero-humidity');
    
    const forecastTodayEl = document.getElementById('forecast-today');
    const forecastWeekEl = document.getElementById('forecast-week');

    const searchInput = document.getElementById('weather-search-input');
    const searchResults = document.getElementById('weather-search-results');

    // --- Highlight Elements ---
    const highlightDateEl = document.getElementById('weather-highlight-date');
    const highlightMaxEl = document.getElementById('weather-highlight-max');
    const highlightMinEl = document.getElementById('weather-highlight-min');
    const highlightVariationEl = document.getElementById('weather-highlight-variation');

    // --- Temperature Unit Toggle Logic ---
    const btnCelsius = document.getElementById('btn-celsius');
    const btnFahrenheit = document.getElementById('btn-fahrenheit');

    // --- Search Functionality ---
    let searchTimeout = null;

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            const query = searchInput.value.trim();
            
            if (query.length < 2) {
                searchResults.classList.add('d-none');
                return;
            }

            searchTimeout = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/geocode/search?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    renderSearchResults(data);
                } catch (err) {
                    console.error("Search failed:", err);
                }
            }, 300);
        });

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('d-none');
            }
        });
    }

    function renderSearchResults(data) {
        if (!searchResults) return;
        
        if (!data || data.length === 0) {
            searchResults.innerHTML = '<div class="p-3 text-muted small">No results found</div>';
        } else {
            searchResults.innerHTML = data.map(item => `
                <div class="search-result-item" data-lat="${item.lat}" data-lon="${item.lon}" data-name="${item.display_name.split(',')[0]}">
                    <i class="fas fa-location-dot"></i>
                    <div class="d-flex flex-column">
                        <span class="fw-bold">${item.display_name.split(',')[0]}</span>
                        <small class="text-muted" style="font-size: 0.75rem;">${item.display_name}</small>
                    </div>
                </div>
            `).join('');

            // Add click events to items
            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.onclick = () => {
                    const lat = item.getAttribute('data-lat');
                    const lon = item.getAttribute('data-lon');
                    const name = item.getAttribute('data-name');
                    
                    searchInput.value = name;
                    searchResults.classList.add('d-none');
                    
                    // Fetch weather for selected city
                    fetchFullForecast(lat, lon);
                };
            });
        }
        
        searchResults.classList.remove('d-none');
    }

    function celsiusToFahrenheit(celsius) {
        return WeatherUtils.celsiusToFahrenheit(celsius);
    }

    function updateDisplayUnits() {
        const tempDisplays = document.querySelectorAll('.temp-display');
        tempDisplays.forEach(display => {
            const celsiusValue = parseFloat(display.getAttribute('data-celsius'));
            if (isNaN(celsiusValue)) return; // Skip if no data

            if (currentUnit === 'F') {
                const fahrenheitValue = celsiusToFahrenheit(celsiusValue);
                display.textContent = `${fahrenheitValue}°`;
            } else {
                display.textContent = `${celsiusValue}°`;
            }
        });

        if (currentUnit === 'F') {
            btnFahrenheit?.classList.remove('bg-light', 'text-dark');
            btnFahrenheit?.classList.add('text-white');
            if(btnFahrenheit) btnFahrenheit.style.backgroundColor = '#6937F5';

            btnCelsius?.classList.remove('text-white');
            btnCelsius?.classList.add('bg-light', 'text-dark');
            if(btnCelsius) btnCelsius.style.backgroundColor = ''; 
        } else {
            btnCelsius?.classList.remove('bg-light', 'text-dark');
            btnCelsius?.classList.add('text-white');
            if(btnCelsius) btnCelsius.style.backgroundColor = '#6937F5';

            btnFahrenheit?.classList.remove('text-white');
            btnFahrenheit?.classList.add('bg-light', 'text-dark');
            if(btnFahrenheit) btnFahrenheit.style.backgroundColor = '';
        }
    }

    if (btnCelsius && btnFahrenheit) {
        btnCelsius.addEventListener('click', function() {
            currentUnit = 'C';
            updateDisplayUnits();
        });

        btnFahrenheit.addEventListener('click', function() {
            currentUnit = 'F';
            updateDisplayUnits();
        });
    }

    // --- API Fetching Logic ---

    async function fetchFullForecast(lat, lon, silent = false) {
        try {
            const response = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
            if (!response.ok) throw new Error('Weather API failed');
            const data = await response.json();
            
            // Save to cache
            localStorage.setItem('synocast_full_forecast_cache', JSON.stringify(data));

            currentData = data.current;
            forecastData = data.forecast;

            // Remove skeletons (only if not silent)
            if (!silent) {
                document.querySelectorAll('.skeleton').forEach(el => {
                    el.classList.remove('skeleton');
                    el.classList.remove('skeleton-text');
                    el.classList.remove('w-50');
                    el.classList.remove('w-75');
                });
                document.querySelectorAll('.skeleton-icon').forEach(el => el.classList.remove('skeleton-icon'));
                document.querySelectorAll('.skeleton-card').forEach(el => el.classList.remove('skeleton-card'));
            }

            updateCurrentWeather(data.current, data.forecast);
            updateHourlyForecast(data.forecast, data.current.timezone);
            updateDailyForecast(data.forecast, data.current.timezone);
            updateAQI(data.pollution);
            
            // Re-run unit update to ensure new data respects current selection
            updateDisplayUnits();

        } catch (error) {
            console.error(error);
            if(!silent && cityEl) {
                cityEl.classList.remove('skeleton'); 
                cityEl.textContent = "Error loading weather";
            }
        }
    }

    function updateAQI(pollution) {
        if (!pollution || !pollution.list || !pollution.list[0]) return;
        
        const aqi = pollution.list[0].main.aqi;
        const aqiValueEl = document.getElementById('weather-aqi-value');
        const aqiDescEl = document.getElementById('weather-aqi-description');
        
        const aqiMap = {
            1: { label: "Good", color: "#2dce89", text: "Air is clean and healthy." },
            2: { label: "Fair", color: "#fb6340", text: "Acceptable air quality." },
            3: { label: "Moderate", color: "#ffd600", text: "Sensitive groups should take care." },
            4: { label: "Poor", color: "#f5365c", text: "Unhealthy for many people." },
            5: { label: "Very Poor", color: "#825ee4", text: "Health warning of emergency conditions." }
        };
        
        const status = aqiMap[aqi] || { label: "Unknown", color: "#adb5bd", text: "Data unavailable" };
        
        if (aqiValueEl) {
            aqiValueEl.textContent = status.label;
            aqiValueEl.style.color = status.color;
        }
        if (aqiDescEl) {
            aqiDescEl.textContent = status.text;
        }
    }

    function updateCurrentWeather(current, forecast) {
        if (!current) return;

        // Location Name (API might just return city name)
        if(cityEl) cityEl.textContent = current.name;
        if(countryEl) countryEl.textContent = current.sys.country; // Country code

        // Date
        const now = new Date();
        const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
        if(dateHeaderEl) dateHeaderEl.textContent = now.toLocaleDateString('en-US', options);

        // Temp
        const temp = Math.round(current.main.temp);
        if(heroTempEl) {
            heroTempEl.setAttribute('data-celsius', temp);
            heroTempEl.textContent = `${temp}°`;
        }

        // Condition
        if (current.weather && current.weather[0]) {
            const w = current.weather[0];
            if(heroConditionEl) heroConditionEl.textContent = w.description.charAt(0).toUpperCase() + w.description.slice(1);
            
            // Map icons (Centralized)
            const iconClass = WeatherUtils.getIconClass(w.id, w.icon);
            if(heroIconEl) heroIconEl.className = `fas ${iconClass} fa-4x mb-2`;
        }

        // Details
        if(windEl) windEl.textContent = WeatherUtils.formatWind(current.wind.speed);
        if(humidityEl) humidityEl.textContent = `${current.main.humidity}%`;
        
        // Accurate Max/Min from next 24h forecast
        let dailyMax = current.main.temp_max;
        let dailyMin = current.main.temp_min;

        if (forecast && forecast.list) {
            const next24h = forecast.list.slice(0, 8);
            dailyMax = Math.max(...next24h.map(i => i.main.temp_max));
            dailyMin = Math.min(...next24h.map(i => i.main.temp_min));
        }

        const roundedMax = Math.round(dailyMax);
        const roundedMin = Math.round(dailyMin);
        const variation = Math.round(dailyMax - dailyMin);

        if(maxTempEl) {
            maxTempEl.setAttribute('data-celsius', roundedMax);
            maxTempEl.textContent = `${roundedMax}°`;
        }
        if(minTempEl) {
             minTempEl.setAttribute('data-celsius', roundedMin);
             minTempEl.textContent = `${roundedMin}°`;
        }

        // Update Highlights Section
        if (highlightDateEl) {
            highlightDateEl.textContent = now.toLocaleDateString('en-US', options);
        }
        if (highlightMaxEl) {
            highlightMaxEl.setAttribute('data-celsius', roundedMax);
            highlightMaxEl.textContent = `${roundedMax}°`;
        }
        if (highlightMinEl) {
            highlightMinEl.setAttribute('data-celsius', roundedMin);
            highlightMinEl.textContent = `${roundedMin}°`;
        }
        if (highlightVariationEl) {
            highlightVariationEl.setAttribute('data-celsius', variation);
            highlightVariationEl.textContent = `${variation}°`;
        }
    }

    function updateHourlyForecast(forecast, timezoneOffset) {
        if(!forecastTodayEl || !forecast.list) return;
        forecastTodayEl.innerHTML = '';
        
        // Next 6 items (3-hour intervals)
        const list = forecast.list.slice(0, 6);
        
        list.forEach((item, index) => {
            const temp = Math.round(item.main.temp);
            const pop = Math.round(item.pop * 100); // Probability of precipitation
            
            // Time
            const date = new Date((item.dt + timezoneOffset) * 1000); // Approx local time
            // Note: OWM timezone is offset in seconds. JS Date uses ms. 
            // We need to account for local browser offset to get "UTC" then add OWM offset.
            // Simplified:
            const d = new Date(item.dt * 1000);
            const localD = new Date(d.getTime() + (new Date().getTimezoneOffset() * 60000) + (timezoneOffset * 1000));
            const timeStr = localD.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
            
            // Icon
            const iconClass = WeatherUtils.getIconClass(item.weather[0].id, item.weather[0].icon);

            const activeClass = index === 0 ? 'active-forecast' : '';
            const borderStyle = index === 0 ? 'border: 2px solid #6937F5;' : 'border: 1px solid #eee;';

            const card = document.createElement('div');
            card.className = `card border-0 rounded-4 p-3 flex-shrink-0 ${activeClass}`;
            card.style = `width: 160px; ${borderStyle}`;
            card.innerHTML = `
                <div class="card-body p-0 d-flex flex-column justify-content-between h-100">
                  <div>
                    <p class="small fw-bold mb-1">${index === 0 ? 'Now' : timeStr}</p>
                    <p class="small text-muted mb-2">${item.weather[0].main}</p>
                  </div>
                  <div class="d-flex justify-content-between align-items-end mt-3">
                    <div>
                      <div class="d-flex align-items-center gap-1 small fw-bold text-primary">
                        <i class="fas fa-thermometer-half"></i> <span class="temp-display" data-celsius="${temp}">${temp}°</span>
                      </div>
                      <div class="d-flex align-items-center gap-1 small text-primary">
                        <i class="fas fa-tint"></i> ${pop}%
                      </div>
                    </div>
                     <i class="fas ${iconClass} fa-2x text-muted"></i>
                  </div>
                </div>
            `;
            forecastTodayEl.appendChild(card);
        });
    }

    function updateDailyForecast(forecast, timezoneOffset) {
        if(!forecastWeekEl || !forecast.list) return;
        forecastWeekEl.innerHTML = '';
        
        // Aggregate daily data (High/Low)
        // OWM provides 3-hour steps. We identify days by date string.
        const daily = {};
        
        forecast.list.forEach(item => {
            const d = new Date(item.dt * 1000);
            const localD = new Date(d.getTime() + (new Date().getTimezoneOffset() * 60000) + (timezoneOffset * 1000));
            const dayKey = localD.toDateString(); // "Sat Sep 27 2024"
            
            if (!daily[dayKey]) {
                daily[dayKey] = {
                    min: item.main.temp_min,
                    max: item.main.temp_max,
                    weather: item.weather[0],
                    pop: item.pop,
                    dateObj: localD
                };
            } else {
                daily[dayKey].min = Math.min(daily[dayKey].min, item.main.temp_min);
                daily[dayKey].max = Math.max(daily[dayKey].max, item.main.temp_max);
                daily[dayKey].pop = Math.max(daily[dayKey].pop, item.pop); // Max prob of rain
            }
        });

        const distinctDays = Object.values(daily).slice(0, 7); // Show 7 days

        distinctDays.forEach(day => {
            const dayName = day.dateObj.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' });
            const timeStr = "12:00"; // Generic for daily
            const temp = Math.round(day.max);
            const pop = Math.round(day.pop * 100);
            
             // Icon
            const iconClass = WeatherUtils.getIconClass(day.weather.id, day.weather.icon);

            const card = document.createElement('div');
            card.className = `card border-0 rounded-4 p-3 flex-shrink-0`;
            card.style = `width: 160px; border: 1px solid #eee;`;
            card.innerHTML = `
                <div class="card-body p-0 d-flex flex-column justify-content-between h-100">
                  <div>
                    <p class="small fw-bold mb-1">${dayName}</p>
                    <p class="small text-muted mb-2">${day.weather.main}</p>
                  </div>
                  <div class="d-flex justify-content-between align-items-end mt-3">
                    <div>
                      <div class="d-flex align-items-center gap-1 small fw-bold text-primary">
                        <i class="fas fa-thermometer-half"></i> <span class="temp-display" data-celsius="${temp}">${temp}°</span>
                      </div>
                      <div class="d-flex align-items-center gap-1 small text-primary">
                        <i class="fas fa-tint"></i> ${pop}%
                      </div>
                    </div>
                    <i class="fas ${iconClass} fa-2x text-muted"></i>
                  </div>
                </div>
            `;
            forecastWeekEl.appendChild(card);
        });
    }

    // --- Tab Switching Logic (Preserved) ---
    const tabToday = document.getElementById('tab-today');
    const tabWeek = document.getElementById('tab-week');

    function switchTab(tab) {
        if (tab === 'today') {
            forecastTodayEl?.classList.remove('d-none');
            forecastWeekEl?.classList.add('d-none');
            tabToday?.classList.remove('text-muted');
             tabToday?.classList.add('text-dark');
            if(tabToday) tabToday.style.opacity = '1';
            tabWeek?.classList.remove('text-dark');
            tabWeek?.classList.add('text-muted');
             if(tabWeek) tabWeek.style.opacity = '0.5';
        } else {
            forecastWeekEl?.classList.remove('d-none');
             forecastTodayEl?.classList.add('d-none');
            tabWeek?.classList.remove('text-muted');
             tabWeek?.classList.add('text-dark');
            if(tabWeek) tabWeek.style.opacity = '1';
            tabToday?.classList.remove('text-dark');
             tabToday?.classList.add('text-muted');
            if(tabToday) tabToday.style.opacity = '0.5';
        }
    }

    if (tabToday && tabWeek) {
        tabToday.addEventListener('click', () => switchTab('today'));
        tabWeek.addEventListener('click', () => switchTab('week'));
    }

    // --- Initialization ---
    // Check for cached data first
    const cachedData = JSON.parse(localStorage.getItem('synocast_full_forecast_cache'));
    if (cachedData) {
        currentData = cachedData.current;
        forecastData = cachedData.forecast;
        
        // Remove skeletons immediately
        document.querySelectorAll('.skeleton').forEach(el => el.classList.remove('skeleton', 'skeleton-text', 'w-50', 'w-75'));
        document.querySelectorAll('.skeleton-icon').forEach(el => el.classList.remove('skeleton-icon'));
        document.querySelectorAll('.skeleton-card').forEach(el => el.classList.remove('skeleton-card'));

        updateCurrentWeather(cachedData.current, cachedData.forecast);
        updateHourlyForecast(cachedData.forecast, cachedData.current.timezone);
        updateDailyForecast(cachedData.forecast, cachedData.current.timezone);
        updateAQI(cachedData.pollution);
        updateDisplayUnits();
    }

    // Listen for global location grant (faster and unified)
    window.addEventListener('synocast_location_granted', (e) => {
        const { lat, lon, isCached } = e.detail;
        fetchFullForecast(lat, lon, !!isCached);
    });

    // Immediate check if location handler already resolved
    if (window.synocast_current_loc) {
        const { lat, lon, isCached } = window.synocast_current_loc;
        fetchFullForecast(lat, lon, !!isCached);
    }

    // Fallback or Initial check if already granted
    setTimeout(async () => {
        // If we still have London coordinates (51.505, -0.09) or no data at all
        const isLondon = currentData && Math.abs(currentData.coord.lat - 51.505) < 0.01;
        
        if ((!currentData || isLondon) && !window.synocast_current_loc) {
            console.log("No specific location found, trying IP fallback...");
            try {
                const ipRes = await fetch('/api/ip-location');
                const ipData = await ipRes.json();
                
                if (ipData.status === 'success') {
                    console.log("Using IP-based location fallback:", ipData.city);
                    fetchFullForecast(ipData.lat, ipData.lon, true);
                } else {
                    throw new Error("IP Geolocation failed");
                }
            } catch (err) {
                if (!currentData) {
                    console.warn("Falling back to London (Ultimate Fallback)");
                    fetchFullForecast(51.505, -0.09);
                }
            }
        }
    }, 4500); // Faster fallback check
});
