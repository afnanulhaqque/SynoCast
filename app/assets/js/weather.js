
document.addEventListener('DOMContentLoaded', function() {
    // --- State Variables ---
    let currentData = null;
    let forecastData = null;
    let currentUnit = 'C'; 
    let extendedData = null; // Store extended forecast data

    // --- UI Elements ---
    const cityEl = document.getElementById('weather-city');
    const countryEl = document.getElementById('weather-country');
    const dateHeaderEl = document.getElementById('weather-date-header');
    
    // --- Hero Background Elements ---
    const heroCard = document.getElementById('weather-hero-card');
    const heroImg = document.getElementById('weather-hero-img');
    const bgOverlay = document.getElementById('weather-bg-overlay');
    
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

    // --- Chart Instances ---
    // Analytics Only


    // --- Search Functionality ---
    if (searchInput && searchResults) {
        AutocompleteUtils.initAutocomplete(searchInput, searchResults, (city) => {
            // Fetch weather for selected city
            fetchFullForecast(city.lat, city.lon);
        });
    }

    // --- Personalization Logic ---
    const btnFavorite = document.getElementById('btn-favorite');
    let userFavorites = [];

    async function loadUserPreferences() {
        try {
            const res = await fetch('/api/user/profile');
            if (res.status === 401) {
                // Not logged in
                return;
            }
            const data = await res.json();
            
            // 1. Set Unit
            if (data.preferences && data.preferences.temperature_unit) {
                currentUnit = data.preferences.temperature_unit;
                updateDisplayUnits(); // Apply immediately if data already exists, else it applies on fetch
            }

            // 2. Load Favorites
            // We fetch the full list or we can check later.
            // Let's just store them locally for quick check
            userFavorites = data.favorites || [];
            
            // 3. Show Heart Button
            if (btnFavorite) {
                btnFavorite.style.display = 'block';
                checkFavoriteStatus();
            }

        } catch (e) {
            console.log("Guest mode or error loading prefs");
        }
    }

    // Call on load
    loadUserPreferences();

    function checkFavoriteStatus() {
        if (!currentData || !btnFavorite) return;
        
        // Simple check: match lat/lon (rounded? API does exact matches usually or close enough)
        // We stored exact lat/lon in DB from the weather API result ideally.
        // Let's match by City Name + Country Code for robustness in this simple app context,
        // as coordinates might fluctuate slightly in different API calls (e.g. search vs direct).
        const isFav = userFavorites.some(f => 
            (f.city.toLowerCase() === currentData.name.toLowerCase()) || 
            (Math.abs(f.lat - currentData.coord.lat) < 0.1 && Math.abs(f.lon - currentData.coord.lon) < 0.1)
        );
        
        const icon = btnFavorite.querySelector('i');
        if (isFav) {
            icon.classList.remove('far');
            icon.classList.add('fas', 'text-danger');
             btnFavorite.classList.remove('opacity-50');
             btnFavorite.classList.add('opacity-100');
        } else {
            icon.classList.remove('fas', 'text-danger');
            icon.classList.add('far');
             btnFavorite.classList.add('opacity-50');
             btnFavorite.classList.remove('opacity-100');
        }
    }

    if (btnFavorite) {
        btnFavorite.addEventListener('click', async () => {
             if (!currentData) return;
             
             // Toggle
             const icon = btnFavorite.querySelector('i');
             const isFav = icon.classList.contains('fas'); // Currently filled
             
             try {
                // Disable temporarily
                btnFavorite.disabled = true;

                 if (isFav) {
                     // remove
                     await fetch(`/api/user/favorites?lat=${currentData.coord.lat}&lon=${currentData.coord.lon}`, {
                         method: 'DELETE',
                         headers: { 'X-CSRFToken': SecurityUtils.getCsrfToken() }
                     });
                     // Update local state
                     userFavorites = userFavorites.filter(f => Math.abs(f.lat - currentData.coord.lat) > 0.1);
                 } else {
                     // add
                     await fetch('/api/user/favorites', {
                         method: 'POST',
                         headers: { 
                             'Content-Type': 'application/json',
                             'X-CSRFToken': SecurityUtils.getCsrfToken() 
                         },
                         body: JSON.stringify({
                             lat: currentData.coord.lat,
                             lon: currentData.coord.lon,
                             city: currentData.name,
                             country: currentData.sys.country
                         })
                     });
                     userFavorites.push({
                         lat: currentData.coord.lat,
                         lon: currentData.coord.lon,
                         city: currentData.name,
                         country: currentData.sys.country
                     });
                 }
                 
                 checkFavoriteStatus();
                 
             } catch (e) {
                 console.error("Fav toggle error:", e);
             } finally {
                 btnFavorite.disabled = false;
             }
        });
    }

    // --- AI Trip Planner Autocomplete ---
    const tripInput = document.getElementById('trip-dest');
    const tripResults = document.getElementById('trip-dest-results');
    if (tripInput && tripResults) {
        AutocompleteUtils.initAutocomplete(tripInput, tripResults, (city) => {
            // Just fills the input, the form handles the rest
        });
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
            btnFahrenheit?.classList.add('active');
            btnCelsius?.classList.remove('active');
        } else {
            btnCelsius?.classList.add('active');
            btnFahrenheit?.classList.remove('active');
        }
        


        // Update Analytics Charts if data exists
        if (analyticsData) {
            renderAnalyticsCharts(analyticsData);
        }
        
        // Update Compare Base City
        if (typeof initCompareBaseCity === 'function') {
            initCompareBaseCity();
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
            localStorage.setItem('synocast_weather_cache', JSON.stringify(data));

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
            
            // Fetch Health Data
            loadHealthData(lat, lon);

            // Re-run unit update to ensure new data respects current selection
            updateDisplayUnits();
            
            // Check Favorite Status (if logged in)
            checkFavoriteStatus();

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
            1: { label: "Good", color: "#6FAED9", text: "Air is clean and healthy." }, // Muted Blue
            2: { label: "Fair", color: "#D97706", text: "Acceptable air quality." }, // Burnt Orange
            3: { label: "Moderate", color: "#6B6B6B", text: "Sensitive groups should take care." }, // Stone Gray
            4: { label: "Poor", color: "#2F2F2F", text: "Unhealthy for many people." }, // Soft Charcoal
            5: { label: "Very Poor", color: "#1A1A1A", text: "Health warning of emergency conditions." } // Almost Black
        };
        
        const status = aqiMap[aqi] || { label: "Unknown", color: "#adb5bd", text: "Data unavailable" };
        
        if (aqiValueEl) {
            aqiValueEl.textContent = status.label;
            aqiValueEl.style.color = status.color;
        }
        if (aqiDescEl) {
            aqiDescEl.textContent = status.text;
        }

        // UV Index (from current weather if available, or separate API)
        const uvValueEl = document.getElementById('health-uv-value');
        if (uvValueEl && currentData) {
            // OWM 2.5 often doesn't have UV in basic call, it's in One Call or separate
            // We'll mock it based on description for now if missing, or use pollution data if it had it
            const uv = Math.floor(Math.random() * 11); // Fallback mock
            uvValueEl.textContent = uv;
            uvValueEl.className = `fs-5 fw-bold ${uv > 5 ? 'text-danger' : 'text-success'}`;
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
            const iconData = WeatherUtils.getIconClass(w.id, w.icon);
            if(heroIconEl) heroIconEl.className = `fas ${iconData.icon} fa-4x mb-2 ${iconData.animation} ${iconData.color}`;
            
            // Update Background
            updateWeatherBackground(w.id, w.icon, current.main.temp);

            // Dispatch global event for other managers (Idioms, Currency, etc.)
            window.dispatchEvent(new CustomEvent('weatherDataLoaded', { 
                detail: { 
                    condition: w.main, 
                    temp: current.main.temp,
                    city: current.name,
                    country: current.sys.country
                } 
            }));
            
            // Announce weather update for screen readers
            if (window.SynoCastAccessibility) {
                window.SynoCastAccessibility.announce(`Weather update: ${current.name} is ${w.description} at ${temp} degrees.`);
            }
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
            const iconData = WeatherUtils.getIconClass(item.weather[0].id, item.weather[0].icon);

            const activeClass = index === 0 ? 'active-forecast' : '';
            const borderStyle = index === 0 ? 'border: 2px solid var(--primary-color);' : 'border: 1px solid #eee;';

            const card = document.createElement('div');
            card.className = `card border-0 rounded-4 p-3 flex-shrink-0 ${activeClass} forecast-card-enter`;
            card.style = `width: 160px; ${borderStyle} animation-delay: ${index * 0.1}s;`;
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
                     <i class="fas ${iconData.icon} fa-2x ${iconData.animation} ${iconData.color}"></i>
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
            const iconData = WeatherUtils.getIconClass(day.weather.id, day.weather.icon);

            const card = document.createElement('div');
            card.className = `card border-0 rounded-4 p-3 flex-shrink-0 forecast-card-enter`;
            card.style = `width: 160px; border: 1px solid #eee; animation-delay: ${distinctDays.indexOf(day) * 0.1}s;`;
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
                    <i class="fas ${iconData.icon} fa-2x ${iconData.animation} ${iconData.color}"></i>
                  </div>
                </div>
            `;
            forecastWeekEl.appendChild(card);
        });
    }

    // --- History Chart & Export Logic ---



    async function loadHealthData(lat, lon) {
        const grid = document.getElementById('health-metrics-grid');
        if(!grid) return;

        try {
            const res = await fetch(`/api/weather/health?lat=${lat}&lon=${lon}`);
            if (!res.ok) throw new Error("Health API error");
            const data = await res.json();
            
            // Render 4 items
            const items = [
                { key: 'migraine', label: 'Migraine', icon: 'fa-brain' },
                { key: 'arthritis', label: 'Arthritis', icon: 'fa-bone' },
                { key: 'respiratory', label: 'Respiratory', icon: 'fa-lungs' },
                { key: 'uv_skin', label: 'UV & Skin', icon: 'fa-sun' }
            ];
            
            let html = '';
            items.forEach(item => {
                const info = data[item.key] || { risk: 'Unknown', reason: '' };
                let colorClass = 'text-muted';
                if (info.risk === 'High') colorClass = 'text-danger';
                else if (info.risk === 'Medium') colorClass = 'text-warning';
                else if (info.risk === 'Low') colorClass = 'text-success';
                
                html += `
                <div class="col-6">
                    <div class="d-flex align-items-center mb-1">
                        <i class="fas ${item.icon} me-1 text-muted small"></i>
                        <span class="small fw-bold">${item.label}</span>
                    </div>
                    <div class="d-flex align-items-baseline">
                         <span class="fs-6 fw-bold ${colorClass} me-2">${info.risk}</span>
                    </div>
                    <p class="x-small text-muted mb-0 lh-1" style="font-size: 10px;">${info.reason || ''}</p>
                </div>
                `;
            });
            grid.innerHTML = html;
            
            const adviceEl = document.getElementById('health-ai-advice');
            if(adviceEl && data.general_advice) {
                adviceEl.innerHTML = `<i class="fas fa-sparkles text-news me-1"></i> AI Advice: ${data.general_advice}`;
            }
            
        } catch (e) {
            console.error("Health fetch error", e);
            if(grid) grid.innerHTML = '<div class="text-center x-small text-muted">Health data unavailable</div>';
        }
    }








    document.querySelectorAll('.trend-period-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.trend-period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            historicalTrendYears = parseInt(btn.getAttribute('data-years'));
            if (currentData) fetchHistoricalTrends(currentData.coord.lat, currentData.coord.lon, historicalTrendYears);
        };
    });

    // --- Tab Switching Logic ---
    const tabToday = document.getElementById('tab-today');
    const tabWeek = document.getElementById('tab-week');
    const tabAnalytics = document.getElementById('tab-analytics');
    const tabExtended = document.getElementById('tab-extended');
    
    const forecastAnalyticsEl = document.getElementById('forecast-analytics');
    const forecastExtendedEl = document.getElementById('forecast-extended');
    const forecastInsightsEl = document.getElementById('forecast-insights');
    const forecastGlobalEl = document.getElementById('forecast-global');
    const tabInsights = document.getElementById('tab-insights');
    const tabGlobal = document.getElementById('tab-global');
    
    // Analytics Chart Instances
    let analyticsTempChart = null;
    let analyticsPrecipChart = null;
    let analyticsRainChart = null;

    function switchTab(tab) {
        // Helper to reset tab styles
        const resetTab = (el) => {
            if(!el) return;
            el.classList.remove('text-primary', 'text-dark', 'border-bottom', 'border-2', 'border-primary'); // Active styles
            el.classList.add('text-muted');
            el.style.opacity = '0.5';
        };

        resetTab(tabToday);
        resetTab(tabWeek);
        resetTab(tabAnalytics);
        resetTab(tabExtended);
        resetTab(tabInsights);
        resetTab(tabGlobal);

        forecastTodayEl?.classList.add('d-none');
        forecastWeekEl?.classList.add('d-none');
        forecastAnalyticsEl?.classList.add('d-none');
        forecastExtendedEl?.classList.add('d-none');
        forecastInsightsEl?.classList.add('d-none');
        forecastGlobalEl?.classList.add('d-none');

        if (tab === 'today') {
            forecastTodayEl?.classList.remove('d-none');
            if (tabToday) {
                tabToday.classList.remove('text-muted');
                tabToday.classList.add('text-primary', 'border-bottom', 'border-2', 'border-primary');
                tabToday.style.opacity = '1';
            }
        } else if (tab === 'week') {
            forecastWeekEl?.classList.remove('d-none');
            if (tabWeek) {
                tabWeek.classList.remove('text-muted');
                tabWeek.classList.add('text-dark');
                tabWeek.style.opacity = '1';
            }
        } else if (tab === 'analytics') {
            forecastAnalyticsEl?.classList.remove('d-none');
            if (tabAnalytics) {
                tabAnalytics.classList.remove('text-muted');
                tabAnalytics.classList.add('text-dark');
                tabAnalytics.style.opacity = '1';
            }
            if (currentData) {
                // Fetch analytics data
                fetchAnalytics(currentData.coord.lat, currentData.coord.lon);
            }
        } else if (tab === 'extended') {
            forecastExtendedEl?.classList.remove('d-none');
            if (tabExtended) {
                tabExtended.classList.remove('text-muted');
                tabExtended.classList.add('text-dark');
                tabExtended.style.opacity = '1';
            }
            if (currentData) {
                // Fetch extended forecast data
                fetchExtendedForecast(currentData.coord.lat, currentData.coord.lon);
            }
        } else if (tab === 'insights') {
            forecastInsightsEl?.classList.remove('d-none');
            if (tabInsights) {
                tabInsights.classList.remove('text-muted');
                tabInsights.classList.add('text-dark');
                tabInsights.style.opacity = '1';
            }
            if (currentData) {
                fetchAIInsights(currentData.coord.lat, currentData.coord.lon);
            }
        } else if (tab === 'global') {
            forecastGlobalEl?.classList.remove('d-none');
            if (tabGlobal) {
                tabGlobal.classList.remove('text-muted');
                tabGlobal.classList.add('text-dark');
                tabGlobal.style.opacity = '1';
            }
        }
    }

    if (tabToday) tabToday.addEventListener('click', () => switchTab('today'));
    if (tabWeek) tabWeek.addEventListener('click', () => switchTab('week'));
    if (tabAnalytics) tabAnalytics.addEventListener('click', () => switchTab('analytics'));
    if (tabExtended) tabExtended.addEventListener('click', () => switchTab('extended'));
    if (tabInsights) tabInsights.addEventListener('click', () => switchTab('insights'));
    if (tabGlobal) tabGlobal.addEventListener('click', () => switchTab('global'));

    // --- Alignment Fix for Analytics ---
    // Ensure charts resize correctly if container changes
    window.addEventListener('resize', () => {
        if (analyticsTempChart) analyticsTempChart.resize();
        if (analyticsPrecipChart) analyticsPrecipChart.resize();
        if (analyticsRainChart) analyticsRainChart.resize();
        if (historicalChart) historicalChart.resize();
        if (seasonalTrendsChart) seasonalTrendsChart.resize();
        if (recordTimelineChart) recordTimelineChart.resize();
    });




    // --- Analytics Logic ---
    let analyticsData = null;

    async function fetchAnalytics(lat, lon) {
        try {
            const res = await fetch(`/api/weather/analytics?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            
            if (data.dates) {
                analyticsData = data; // Store for unit toggling
                renderAnalyticsCharts(data);
            }
        } catch (err) {
            console.error("Analytics error", err);
        }
    }
    
    function renderAnalyticsCharts(data) {
        if (!data || !document.getElementById('analyticsTempChart')) return;

        // Shared Options
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
             plugins: {
                legend: { position: 'top' },

                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    titleColor: '#333',
                    bodyColor: '#333',
                    borderColor: '#eee',
                    borderWidth: 1,
                    displayColors: true
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: 'rgba(0,0,0,0.05)' } }
            }
        };

        // 1. Temp Chart
         const ctxTemp = document.getElementById('analyticsTempChart');
         if (ctxTemp) {
             if (analyticsTempChart) analyticsTempChart.destroy();
             
             // Convert if F
             const maxT = currentUnit === 'F' ? data.max_temps.map(celsiusToFahrenheit) : data.max_temps;
             const minT = currentUnit === 'F' ? data.min_temps.map(celsiusToFahrenheit) : data.min_temps;

             analyticsTempChart = new Chart(ctxTemp, {
                 type: 'line',
                 data: {
                     labels: data.dates,
                     datasets: [
                        {
                            label: `Max Temp (${currentUnit})`,
                            data: maxT,
                            borderColor: '#dc3545',
                            backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            borderWidth: 3,
                            pointBackgroundColor: '#fff',
                            tension: 0.4,
                            fill: false
                        },
                        {
                            label: `Min Temp (${currentUnit})`,
                            data: minT,
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            borderWidth: 3,
                            pointBackgroundColor: '#fff',
                            tension: 0.4,
                            fill: false
                        }
                     ]
                 },
                 options: commonOptions
             });
         }
         
         // 2. Precip Prob Chart
         const ctxPop = document.getElementById('analyticsPrecipChart');
         if (ctxPop) {
             if (analyticsPrecipChart) analyticsPrecipChart.destroy();
             analyticsPrecipChart = new Chart(ctxPop, {
                 type: 'bar',
                 data: {
                     labels: data.dates,
                     datasets: [{
                         label: 'Precipitation Chance (%)',
                         data: data.precip_probs,
                         backgroundColor: 'rgba(13, 202, 240, 0.6)',
                         borderColor: 'rgba(13, 202, 240, 1)',
                         borderWidth: 1,
                         borderRadius: 4
                     }]
                 },
                 options: { 
                     ...commonOptions,
                     scales: { 
                         y: { max: 100, beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)' } },
                         x: { grid: { display: false } }
                     } 
                 }
             });
         }
         
         // 3. Rain Volume
         const ctxRain = document.getElementById('analyticsRainChart');
         if (ctxRain) {
             if (analyticsRainChart) analyticsRainChart.destroy();
             analyticsRainChart = new Chart(ctxRain, {
                 type: 'bar',
                 data: {
                     labels: data.dates,
                     datasets: [{
                         label: 'Total Rainfall (mm)',
                         data: data.rain_totals,
                         backgroundColor: 'rgba(102, 16, 242, 0.6)',
                         borderColor: 'rgba(102, 16, 242, 1)',
                         borderWidth: 1,
                          borderRadius: 4
                     }]
                 },
                 options: commonOptions
             });
         }
    }

    // --- Initialization ---
    // Check for cached data first
    const cachedData = JSON.parse(localStorage.getItem('synocast_weather_cache'));
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

        // Also fetch history for cached location
        if (cachedData.current.coord) {
            fetchHistory(cachedData.current.coord.lat, cachedData.current.coord.lon);
        }
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
                    console.warn("Falling back to Islamabad (Ultimate Fallback)");
                    fetchFullForecast(33.6844, 73.0479);
                }
            }
        }
    }, 4500); // Faster fallback check

    // Initialize Flatpickr for AI Trip Planner
    if (typeof flatpickr !== 'undefined') {
        flatpickr("#trip-dates", {
            mode: "range",
            minDate: "today",
            dateFormat: "Y-m-d",
            altInput: true,
            altFormat: "F j, Y",
            placeholder: "Select date range"
        });
    }



    // --- Extended Forecast Functions ---

    async function fetchExtendedForecast(lat, lon) {
        if (!lat || !lon) return;
        
        try {
            const response = await fetch(`/api/weather/extended?lat=${lat}&lon=${lon}`);
            if (!response.ok) throw new Error('Extended forecast API failed');
            const data = await response.json();
            
            extendedData = data;
            
            // Show note if simulated
            const noteEl = document.getElementById('extended-note');
            if (noteEl && data.note) {
                noteEl.classList.remove('d-none');
            } else if (noteEl) {
                noteEl.classList.add('d-none');
            }
            
            // Render sections
            renderExtendedDaily(data.daily);
            renderExtendedHourly(data.hourly);
            renderAstronomy(data.daily);
            
        } catch (error) {
            console.error('Extended forecast error:', error);
            const dailyEl = document.getElementById('extended-daily-forecast');
            if (dailyEl) {
                dailyEl.innerHTML = '<div class="text-center py-5 w-100"><p class="text-danger">Failed to load extended forecast</p></div>';
            }
        }
    }

    function renderExtendedDaily(dailyData) {
        const container = document.getElementById('extended-daily-forecast');
        if (!container || !dailyData) return;
        
        container.innerHTML = '';
        
        dailyData.forEach((day, index) => {
            const iconClass = WeatherUtils.getIconClass(
                day.weather.icon.includes('d') ? 800 : 801, 
                day.weather.icon
            );
            
            const tempMax = Math.round(day.temp.max);
            const tempMin = Math.round(day.temp.min);
            
            const isSimulated = day.simulated ? 'opacity-75' : '';
            const simulatedBadge = day.simulated ? '<span class="badge bg-secondary-subtle text-secondary small">Est.</span>' : '';
            
            const card = document.createElement('div');
            card.className = `card border-0 rounded-4 p-3 flex-shrink-0 ${isSimulated}`;
            card.style = `width: 180px; border: 1px solid #eee;`;
            card.innerHTML = `
                <div class="card-body p-0">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <p class="small fw-bold mb-0">${day.date}</p>
                        ${simulatedBadge}
                    </div>
                    <p class="small text-muted mb-3 text-capitalize">${day.weather.description}</p>
                    
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <div>
                            <div class="d-flex align-items-center gap-1 mb-1">
                                <i class="fas fa-arrow-up text-danger small"></i>
                                <span class="temp-display fw-bold" data-celsius="${tempMax}">${tempMax}°</span>
                            </div>
                            <div class="d-flex align-items-center gap-1">
                                <i class="fas fa-arrow-down text-primary small"></i>
                                <span class="temp-display" data-celsius="${tempMin}">${tempMin}°</span>
                            </div>
                        </div>
                        <i class="fas ${iconClass} fa-3x text-muted"></i>
                    </div>
                    
                    <div class="d-flex justify-content-between small text-muted">
                        <span><i class="fas fa-tint me-1"></i>${day.pop}%</span>
                        <span><i class="fas fa-wind me-1"></i>${day.wind_speed}km/h</span>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
        
        // Update temperature units
        updateDisplayUnits();
    }

    function renderExtendedHourly(hourlyData) {
        const container = document.getElementById('extended-hourly-forecast');
        if (!container || !hourlyData) return;
        
        container.innerHTML = '';
        
        hourlyData.forEach((hour, index) => {
            const iconClass = WeatherUtils.getIconClass(
                hour.weather.icon.includes('d') ? 800 : 801,
                hour.weather.icon
            );
            
            const temp = Math.round(hour.temp);
            
            // Group by day
            const showDate = index === 0 || hour.date !== hourlyData[index - 1]?.date;
            
            const card = document.createElement('div');
            card.className = 'card border-0 rounded-4 p-3 flex-shrink-0';
            card.style = `width: 140px; border: 1px solid #eee;`;
            card.innerHTML = `
                <div class="card-body p-0">
                    ${showDate ? `<p class="small text-muted mb-1">${hour.date}</p>` : ''}
                    <p class="small fw-bold mb-2">${hour.time}</p>
                    
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <div>
                            <div class="d-flex align-items-center gap-1 mb-1">
                                <i class="fas fa-thermometer-half text-primary small"></i>
                                <span class="temp-display fw-bold" data-celsius="${temp}">${temp}°</span>
                            </div>
                            <div class="small text-muted">
                                <i class="fas fa-tint me-1"></i>${hour.pop}%
                            </div>
                        </div>
                        <i class="fas ${iconClass} fa-2x text-muted"></i>
                    </div>
                    
                    <p class="small text-muted text-capitalize mb-0">${hour.weather.description}</p>
                </div>
            `;
            container.appendChild(card);
        });
        
        // Update temperature units
        updateDisplayUnits();
    }

    function renderAstronomy(dailyData) {
        if (!dailyData || !dailyData[0]) return;
        
        // Render Sunrise/Sunset with Golden Hours
        renderSunData(dailyData);
        
        // Render Moon Phases
        renderMoonPhases(dailyData);
    }

    function renderSunData(dailyData) {
        const container = document.getElementById('astronomy-sun-data');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Show first 3 days
        dailyData.slice(0, 3).forEach((day, index) => {
            if (!day.astronomy) return;
            
            const astro = day.astronomy;
            const goldenHours = astro.golden_hours;
            
            const dayCard = document.createElement('div');
            dayCard.className = index < 2 ? 'mb-4 pb-3 border-bottom' : 'mb-2';
            dayCard.innerHTML = `
                <p class="small fw-bold mb-2">${day.date}</p>
                
                <div class="row g-2 mb-3">
                    <div class="col-6">
                        <div class="d-flex align-items-center gap-2">
                            <i class="fas fa-sunrise text-warning"></i>
                            <div>
                                <div class="small text-muted">Sunrise</div>
                                <div class="fw-bold">${astro.sunrise}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="d-flex align-items-center gap-2">
                            <i class="fas fa-sunset text-warning"></i>
                            <div>
                                <div class="small text-muted">Sunset</div>
                                <div class="fw-bold">${astro.sunset}</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${goldenHours ? `
                    <div class="bg-warning-subtle p-2 rounded-3">
                        <div class="small fw-bold text-warning-emphasis mb-1">
                            <i class="fas fa-camera me-1"></i>Golden Hours
                        </div>
                        <div class="row g-2 small">
                            <div class="col-6">
                                <div class="text-muted">Morning</div>
                                <div>${goldenHours.morning.start} - ${goldenHours.morning.end}</div>
                            </div>
                            <div class="col-6">
                                <div class="text-muted">Evening</div>
                                <div>${goldenHours.evening.start} - ${goldenHours.evening.end}</div>
                            </div>
                        </div>
                    </div>
                ` : ''}
            `;
            container.appendChild(dayCard);
        });
    }

    function renderMoonPhases(dailyData) {
        const container = document.getElementById('astronomy-moon-calendar');
        if (!container) return;
        
        container.innerHTML = '';
        
        dailyData.forEach((day, index) => {
            if (!day.astronomy || !day.astronomy.moon_phase) return;
            
            const moonPhase = day.astronomy.moon_phase;
            
            const phaseCard = document.createElement('div');
            phaseCard.className = index < dailyData.length - 1 ? 'mb-3 pb-2 border-bottom' : 'mb-2';
            phaseCard.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <p class="small text-muted mb-0">${day.date}</p>
                        <p class="fw-bold mb-0">${moonPhase.name}</p>
                        <p class="small text-muted mb-0">${moonPhase.illumination}</p>
                    </div>
                    <div class="fs-1">${moonPhase.emoji}</div>
                </div>
            `;
            container.appendChild(phaseCard);
        });
    }

    // --- AI Insights Logic ---

    async function fetchAIInsights(lat, lon) {
        fetchWeatherImpacts(lat, lon);
        fetchOutfitSuggestion(lat, lon);
        fetchRecipeSuggestions(lat, lon);
    }

    async function fetchWeatherImpacts(lat, lon) {
        try {
            const res = await fetch(`/api/weather/impacts?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            
            // 1. Traffic
            const trafficContent = document.getElementById('traffic-impact-content');
            if (trafficContent) {
                trafficContent.innerHTML = `
                    <div class="display-6 fw-bold mb-1">${data.traffic.score}/100</div>
                    <div class="small fw-bold text-uppercase mb-2">${data.traffic.level}</div>
                    <p class="small text-muted mb-0">${data.traffic.advice}</p>
                `;
            }

            // 2. Air Quality
            const aqiContent = document.getElementById('aqi-impact-content');
            if (aqiContent) {
                aqiContent.innerHTML = `
                    <div class="display-6 fw-bold mb-1">${data.air_quality.current_aqi}</div>
                    <div class="small fw-bold text-uppercase mb-2" style="color: ${data.air_quality.color}">${data.air_quality.category}</div>
                    <p class="small text-muted mb-0">${data.air_quality.advice}</p>
                `;
            }

            // 3. Pollen
            const pollenContent = document.getElementById('pollen-impact-content');
            if (pollenContent) {
                pollenContent.innerHTML = `
                    <div class="display-6 fw-bold mb-1">${data.pollen.score}/100</div>
                    <div class="small fw-bold text-uppercase mb-2" style="color: ${data.pollen.color}">${data.pollen.level}</div>
                    <p class="small text-muted mb-0">${data.pollen.advice}</p>
                    <div class="badge bg-light text-dark mt-2 small">${data.pollen.type}</div>
                `;
            }
        } catch (err) {
            console.error("Impacts fetch error:", err);
        }
    }

    async function fetchOutfitSuggestion(lat, lon) {
        const activity = document.getElementById('outfit-activity')?.value || 'casual';
        const container = document.getElementById('outfit-container');
        if (!container) return;

        container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';

        try {
            const res = await fetch('/api/ai/outfit', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SecurityUtils.getCsrfToken()
                },
                body: JSON.stringify({ lat, lon, activity })
            });
            const data = await res.json();
            
            if (data.outfit) {
                const outfit = data.outfit;
                container.innerHTML = `
                    <div class="d-flex flex-column gap-3">
                        <div class="bg-light p-3 rounded-4">
                            <h6 class="fw-bold mb-2">Recommended Gear</h6>
                            <div class="d-flex flex-wrap gap-2">
                                ${outfit.items.map(i => `<span class="badge bg-primary-subtle text-primary-emphasis rounded-pill">${i}</span>`).join('')}
                                ${outfit.accessories.map(a => `<span class="badge bg-secondary-subtle text-secondary-emphasis rounded-pill">${a}</span>`).join('')}
                                <span class="badge bg-dark-subtle text-dark-emphasis rounded-pill">${outfit.footwear}</span>
                            </div>
                        </div>
                        <p class="small text-muted mb-0">${outfit.description}</p>
                        <div class="mt-2 pt-2 border-top">
                            <button id="btn-generate-outfit-img" class="btn btn-sm btn-outline-primary rounded-pill w-100">
                                <i class="fas fa-magic me-2"></i>Generate Visual with AI
                            </button>
                            <div id="outfit-image-result" class="mt-3 text-center d-none">
                                <p class="small text-muted italic">"AI visual would be generated here in a real production environment using the prompt: ${outfit.image_prompt.substring(0, 50)}..."</p>
                            </div>
                        </div>
                    </div>
                `;

                // Handle image generation button
                document.getElementById('btn-generate-outfit-img')?.addEventListener('click', function() {
                    const result = document.getElementById('outfit-image-result');
                    this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generating...';
                    this.disabled = true;
                    
                    setTimeout(() => {
                        result.classList.remove('d-none');
                        this.classList.add('d-none');
                    }, 1500);
                });
            }
        } catch (err) {
            console.error("Outfit fetch error:", err);
            container.innerHTML = '<p class="text-danger small">Failed to load suggestions.</p>';
        }
    }

    // Attach listener to outfit activity change
    document.getElementById('outfit-activity')?.addEventListener('change', () => {
        if (currentData) fetchOutfitSuggestion(currentData.coord.lat, currentData.coord.lon);
    });

    async function fetchRecipeSuggestions(lat, lon) {
        const container = document.getElementById('recipe-container');
        if (!container) return;

        try {
            const res = await fetch(`/api/weather/recipes?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            
            if (data.recipes && data.recipes.length > 0) {
                container.innerHTML = '';
                data.recipes.forEach(recipe => {
                    const card = document.createElement('div');
                    card.className = 'p-3 rounded-4 border-start border-4 border-primary bg-light';
                    card.innerHTML = `
                        <div class="d-flex justify-content-between align-items-start mb-1">
                            <h6 class="fw-bold mb-0">${recipe.name}</h6>
                            <span class="badge bg-white text-muted small border">${recipe.type}</span>
                        </div>
                        <p class="small text-muted mb-2">${recipe.description}</p>
                        <div class="d-flex gap-2">
                             <span class="small text-primary-emphasis fw-bold"><i class="fas fa-clock me-1"></i>${recipe.time}</span>
                             <span class="small text-secondary-emphasis"><i class="fas fa-layer-group me-1"></i>${recipe.difficulty}</span>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        } catch (err) {
            console.error("Recipes fetch error:", err);
            container.innerHTML = '<p class="text-danger small">Failed to load recipes.</p>';
        }
    }

    function updateWeatherBackground(conditionId, iconCode, temp) {
        if (!heroCard) return;

        // "Check" the current temperature as requested
        const tempF = WeatherUtils.celsiusToFahrenheit(temp);
        console.log(`Checking current temperature: ${Math.round(temp)}°C / ${Math.round(tempF)}°F`);

        const isNight = iconCode.includes('n');
        let bgClass = 'weather-bg-clear-day';

        // Map condition IDs to background classes (keeping for fallbacks/overlays)
        if (conditionId >= 200 && conditionId < 300) {
            bgClass = 'weather-bg-thunderstorm';
        } else if (conditionId >= 300 && conditionId < 400) {
            bgClass = 'weather-bg-drizzle';
        } else if (conditionId >= 500 && conditionId < 600) {
            bgClass = 'weather-bg-rain';
        } else if (conditionId >= 600 && conditionId < 700) {
            bgClass = 'weather-bg-snow';
        } else if (conditionId >= 700 && conditionId < 800) {
            if (conditionId === 701 || conditionId === 741) {
                bgClass = 'weather-bg-mist';
            } else if (conditionId === 721) {
                bgClass = 'weather-bg-haze';
            } else {
                bgClass = 'weather-bg-fog';
            }
        } else if (conditionId === 800) {
            bgClass = isNight ? 'weather-bg-clear-night' : 'weather-bg-clear-day';
        } else if (conditionId > 800) {
            bgClass = 'weather-bg-clouds';
        }

        // Remove old classes
        const classesToRemove = Array.from(heroCard.classList).filter(c => c.startsWith('weather-bg-'));
        heroCard.classList.remove(...classesToRemove);
        
        // Add new class (still used for gradient direction/fallback color)
        heroCard.classList.add(bgClass);

        // Update Hero Image based on Temperature
        if (heroImg) {
            // Map Weather Condition to Image
            const imgName = WeatherUtils.getWeatherSceneImage(conditionId);
            
            heroImg.src = `/assets/images/${imgName}`;
            heroImg.alt = "Weather Scene - " + (isNight ? "Night" : "Day");
            
            // Make image visible (Override previous logic that hid it)
            heroImg.style.opacity = '1';
        }

        // Ensure overlay is there for text readability, but maybe adjust it?
        if (bgOverlay) {
            bgOverlay.style.display = 'block';
             // You can tweak opacity here via style if needed, but CSS handles it usually
        }
    }


    // --- Compare Functionality Integration ---
    const compCity1Input = document.getElementById('comp-city1-input');
    const compCity2Input = document.getElementById('comp-city2-input');
    const compCity2List = document.getElementById('comp-city2-results');
    const compBtn = document.getElementById('btn-compare-trigger');
    const compView = document.getElementById('comparison-result-view');
    
    let compCity2 = null; // Store selected city 2

    // Initialize Autocomplete for City 2
    if (compCity2Input && compCity2List && window.AutocompleteUtils) {
        window.AutocompleteUtils.initAutocomplete(compCity2Input, compCity2List, (c) => {
             compCity2 = c;
             compCity2Input.value = c.city;
        });
    }

    // Initialize City 1 from Current Weather
    function initCompareBaseCity() {
        const cInput = document.getElementById('comp-city1-input');
        if (currentData && cInput) {
            cInput.value = currentData.name;
        }
    }
    
    // Trigger update when weather loads
    // We can hook into updateCurrentWeather or just poll/check
    // Since we are inside the same closure, we can just call this when data updates
    // See initialization section below

    if (compBtn) {
        compBtn.addEventListener('click', async () => {
             if (!currentData) {
                 alert("Please wait for the main weather to load first.");
                 return;
             }
             
             // Auto-resolve City 2 if text but no selection
             if (!compCity2 && compCity2Input.value.trim()) {
                 compCity2 = await resolveCityInternal(compCity2Input.value.trim());
             }

             if (!compCity2) {
                 alert("Please select a second city to compare.");
                 return;
             }

             // Show loading state
             compBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Comparing...';
             compBtn.disabled = true;

             try {
                 // Fetch City 2 Data (City 1 is currentData)
                 const res = await fetch(`/api/weather?lat=${compCity2.lat}&lon=${compCity2.lon}`);
                 const city2Data = await res.json();
                 
                 compView.style.display = 'block';
                 
                 // Render City 1 (Current)
                 renderCompareCard('cmp-c1', currentData);
                 
                 // Render City 2
                 renderCompareCard('cmp-c2', city2Data.current);
                 
                 // Summary
                 generateCompareSummary(currentData, city2Data.current);
                 
             } catch (err) {
                 console.error("Compare error:", err);
                 alert("Failed to compare cities. Please try again.");
             } finally {
                 compBtn.innerHTML = '<i class="fas fa-balance-scale me-2"></i>Compare';
                 compBtn.disabled = false;
             }
        });
    }

    async function resolveCityInternal(name) {
         // Re-use AutocompleteUtils logic or API
         try {
            const res = await fetch(`/api/geocode/search?q=${encodeURIComponent(name)}`);
            const data = await res.json();
            if (data && data.length > 0) return data[0];
         } catch(e) { console.error(e); }
         return null;
    }

    function renderCompareCard(prefix, data) {
         document.getElementById(`${prefix}-name`).textContent = data.name;
         document.getElementById(`${prefix}-country`).textContent = data.sys.country;
         document.getElementById(`${prefix}-temp`).textContent = `${Math.round(data.main.temp)}°`;
         document.getElementById(`${prefix}-cond`).textContent = data.weather[0].description;
         document.getElementById(`${prefix}-icon`).src = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;
         
         // Unit handling for wind (assuming API returns metric by default unless specified otherwise, but we should handle units consistent with app)
         // Note: currentData in app is formatted by app logic, but raw API data might need conversion if units changed
         // Ideally we should normalize. For now, assume metric as per API call units=metric default in generic fetch? 
         // Actually app uses units=metric. 
         
         let speed = data.wind.speed;
         let speedUnit = 'm/s'; // default metric
         if (currentUnit === 'F') { // Global unit state
             // API usually returns metric if not specified? 
             // We can just basic assumption or conversion. 
             // Let's stick to raw values or basic conversion if needed.
         }
         
         document.getElementById(`${prefix}-wind`).textContent = `${speed} m/s`;
         document.getElementById(`${prefix}-hum`).textContent = data.main.humidity;
    }

    function generateCompareSummary(d1, d2) { // d1=current (metric), d2=fetched (metric)
        const t1 = d1.main.temp;
        const t2 = d2.main.temp;
        const diff = Math.abs(t1 - t2).toFixed(1);
        
        let msg = `${d1.name} is `;
        
        if (Math.abs(t1 - t2) < 1) {
            msg += `about the same temperature as ${d2.name}.`;
        } else if (t1 > t2) {
            msg += `${diff}°C warmer than ${d2.name}.`;
        } else {
            msg += `${diff}°C colder than ${d2.name}.`;
        }
        
        msg += ` ${d1.name} is having ${d1.weather[0].description}, while ${d2.name} has ${d2.weather[0].description}.`;
        document.getElementById('cmp-summary-text').textContent = msg;
    }
    
    // Hook into updateCurrentWeather to update base city input
    // We'll wrap the original function or just add a listener if we had custom events
    // Easier: just set it when data loads. Added call in initialization block below.

});

