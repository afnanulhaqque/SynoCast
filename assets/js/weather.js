
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

    // --- Chart Instance ---
    let historicalChart = null;
    let historyData = null; // Store for export

    // --- Search Functionality ---
    if (searchInput && searchResults) {
        AutocompleteUtils.initAutocomplete(searchInput, searchResults, (city) => {
            // Fetch weather for selected city
            fetchFullForecast(city.lat, city.lon);
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
        
        // Update History Chart if it exists
        if (historicalChart && historyData) {
            renderHistoryChart(historyData);
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
            
            // Fetch History Data
            fetchHistory(lat, lon);
            
            // Auto-fetch "On This Day" for 5 years ago
            fetchOnThisDay(lat, lon, 5);

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
            const borderStyle = index === 0 ? 'border: 2px solid var(--primary-color);' : 'border: 1px solid #eee;';

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

    // --- History Chart & Export Logic ---

    async function fetchHistory(lat, lon) {
        try {
            const res = await fetch(`/api/weather/history?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            historyData = data;
            renderHistoryChart(data);
        } catch (err) {
            console.error("Failed to fetch history:", err);
        }
    }

    function renderHistoryChart(data) {
        const ctx = document.getElementById('historicalChart');
        if (!ctx) return;

        const labels = data.map(item => item.date);
        const temps = data.map(item => {
            const t = parseFloat(item.temp);
            return currentUnit === 'F' ? WeatherUtils.celsiusToFahrenheit(t) : t;
        });

        if (historicalChart) {
            historicalChart.destroy();
        }

        historicalChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `Avg Temperature (${currentUnit})`,
                    data: temps,
                    borderColor: '#2F2F2F',
                    backgroundColor: 'rgba(47, 47, 47, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#2F2F2F',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: '#fff',
                        titleColor: '#333',
                        bodyColor: '#666',
                        borderColor: '#eee',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `${context.parsed.y}°${currentUnit}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0,0,0,0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            callback: value => `${value}°`
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // --- Export Functionality ---
    const exportJsonBtn = document.getElementById('export-json');
    const exportCsvBtn = document.getElementById('export-csv');

    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', () => {
            if (!historyData) return;
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(historyData, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "weather_history.json");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        });
    }

    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => {
            if (!historyData) return;
            const headers = "Date,Temperature(C),Condition,Humidity(%),Wind(km/h)\n";
            const rows = historyData.map(item => `${item.date},${item.temp},${item.condition},${item.humidity},${item.wind}`).join("\n");
            const csvContent = "data:text/csv;charset=utf-8," + encodeURIComponent(headers + rows);
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", csvContent);
            downloadAnchorNode.setAttribute("download", "weather_history.csv");
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
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

    // --- AI Suite Logic ---

    // 1. AI Trip Planner
    const btnGenerateTrip = document.getElementById('btn-generate-trip');
    if (btnGenerateTrip) {
        btnGenerateTrip.addEventListener('click', async () => {
            const dest = document.getElementById('trip-dest').value;
            const dates = document.getElementById('trip-dates').value;
            const purpose = document.getElementById('trip-purpose').value;
            const resultEl = document.getElementById('trip-plan-result');

            if (!dest || !dates) {
                const errorEl = document.getElementById('trip-error-msg');
                if (errorEl) {
                    errorEl.textContent = "Please enter destination and dates.";
                    errorEl.classList.remove('d-none');
                    setTimeout(() => errorEl.classList.add('d-none'), 5000);
                }
                return;
            }

            resultEl.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">SynoBot is planning your trip...</p></div>';

            try {
                const res = await fetch(`/api/trip_plan?destination=${encodeURIComponent(dest)}&dates=${encodeURIComponent(dates)}&purpose=${encodeURIComponent(purpose)}`);
                const data = await res.json();
                if (data.plan) {
                    resultEl.innerHTML = `<div class="ai-plan-content">${data.plan.replace(/\n/g, '<br>')}</div>`;
                } else {
                    resultEl.innerHTML = `<p class="text-danger">Error: ${data.error || 'Failed to generate plan'}</p>`;
                }
            } catch (err) {
                resultEl.innerHTML = `<p class="text-danger">Failed to connect to AI server.</p>`;
            }
        });
    }

    // 2. Weather Duel
    const btnDuelCompare = document.getElementById('btn-duel-compare');
    if (btnDuelCompare) {
        btnDuelCompare.addEventListener('click', async () => {
            const city1 = document.getElementById('duel-city1').value;
            const city2 = document.getElementById('duel-city2').value;
            const data1El = document.getElementById('duel-data1');
            const data2El = document.getElementById('duel-data2');

            if (!city1 || !city2) {
                alert("Please enter two cities.");
                return;
            }

            data1El.innerHTML = data2El.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>';

            try {
                const res = await fetch(`/api/weather/compare?city1=${encodeURIComponent(city1)}&city2=${encodeURIComponent(city2)}`);
                const data = await res.json();
                
                if (data.city1 && data.city2) {
                    const renderDuel = (cityData) => `
                        <div class="mt-3">
                            <h3 class="fw-bold mb-0">${Math.round(cityData.main.temp)}°C</h3>
                            <p class="text-muted small mb-2">${cityData.weather[0].description}</p>
                            <div class="d-flex justify-content-around small">
                                <span><i class="fas fa-tint me-1"></i>${cityData.main.humidity}%</span>
                                <span><i class="fas fa-wind me-1"></i>${Math.round(cityData.wind.speed * 3.6)}km/h</span>
                            </div>
                        </div>
                    `;
                    data1El.innerHTML = renderDuel(data.city1);
                    data2El.innerHTML = renderDuel(data.city2);
                } else {
                    data1El.innerHTML = data2El.innerHTML = '<span class="text-danger">Error</span>';
                }
            } catch (err) {
                data1El.innerHTML = data2El.innerHTML = '<span class="text-danger">Failed</span>';
            }
        });
    }

    // 3. On This Day (Historical)
    async function fetchOnThisDay(lat, lon, years) {
        console.log(`Fetching On This Day for ${lat}, ${lon} (${years} years ago)`);
        const contentEl = document.getElementById('history-insight-content');
        
        if (!lat || !lon) {
            if (currentData && currentData.coord) {
                lat = currentData.coord.lat;
                lon = currentData.coord.lon;
            } else {
                return;
            }
        }
        if (!contentEl) return;

        contentEl.innerHTML = '<div class="col text-center py-5 w-100"><div class="spinner-border text-primary" role="status"></div></div>';

        try {
            const res = await fetch(`/api/weather/historical?lat=${lat}&lon=${lon}&years=${years}`);
            const data = await res.json();
            
            if (data.temp_max !== undefined) {
                contentEl.innerHTML = `
                    <div class="col text-center">
                        <div class="p-3 bg-white rounded-4 shadow-sm h-100 border">
                            <p class="small text-muted mb-1">Max Temp</p>
                            <h4 class="fw-bold text-danger mb-0">${Math.round(data.temp_max)}°C</h4>
                        </div>
                    </div>
                    <div class="col text-center">
                        <div class="p-3 bg-white rounded-4 shadow-sm h-100 border">
                            <p class="small text-muted mb-1">Min Temp</p>
                            <h4 class="fw-bold text-primary mb-0">${Math.round(data.temp_min)}°C</h4>
                        </div>
                    </div>
                    <div class="col text-center">
                        <div class="p-3 bg-white rounded-4 shadow-sm h-100 border">
                            <p class="small text-muted mb-1">Precipitation</p>
                            <h4 class="fw-bold text-info mb-0">${data.rain}mm</h4>
                        </div>
                    </div>
                `;
            } else if (data.data) { // OWM Response
                 const main = data.data.data[0];
                 contentEl.innerHTML = `
                    <div class="col text-center">
                        <div class="p-3 bg-white rounded-4 shadow-sm h-100 border">
                            <p class="small text-muted mb-1">Temp</p>
                            <h4 class="fw-bold text-danger mb-0">${Math.round(main.temp)}°C</h4>
                        </div>
                    </div>
                    <div class="col text-center">
                        <div class="p-3 bg-white rounded-4 shadow-sm h-100 border">
                            <p class="small text-muted mb-1">Condition</p>
                            <h4 class="fw-bold text-primary mb-0">${main.weather[0].main}</h4>
                        </div>
                    </div>
                `;
            } else {
                contentEl.innerHTML = '<p class="text-center w-100 py-4 opacity-50">No historical data available for this date.</p>';
            }
        } catch (err) {
            contentEl.innerHTML = '<p class="text-center w-100 py-4 text-danger">Failed to fetch historical data.</p>';
        }
    }

    document.querySelectorAll('.hist-year-btn').forEach(btn => {
        btn.onclick = () => {
             document.querySelectorAll('.hist-year-btn').forEach(b => b.classList.remove('active'));
             btn.classList.add('active');
             const years = btn.getAttribute('data-years');
             if (currentData) fetchOnThisDay(currentData.coord.lat, currentData.coord.lon, years);
        };
    });

    // 4. Community Verification
    document.querySelectorAll('.verify-btn').forEach(btn => {
        btn.onclick = async () => {
            const condition = btn.getAttribute('data-condition');
            const statusEl = document.getElementById('verify-status');
            
            if (!currentData) return;

            try {
                const res = await fetch('/api/report_weather', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="_csrf_token"]').content },
                    body: JSON.stringify({
                        lat: currentData.coord.lat,
                        lon: currentData.coord.lon,
                        city: currentData.name,
                        condition: condition,
                        api_condition: currentData.weather[0].main
                    })
                });
                const data = await res.json();
                statusEl.className = 'alert alert-success mt-3 small';
                statusEl.textContent = data.message;
                statusEl.classList.remove('d-none');
            } catch (err) {
                console.error("Verification failed:", err);
            }
        };
    });

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
});
