
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

    // --- Highlight Elements ---
    const highlightDateEl = document.getElementById('weather-highlight-date');
    const highlightMaxEl = document.getElementById('weather-highlight-max');
    const highlightMinEl = document.getElementById('weather-highlight-min');
    const highlightVariationEl = document.getElementById('weather-highlight-variation');

    // --- Temperature Unit Toggle Logic ---
    const btnCelsius = document.getElementById('btn-celsius');
    const btnFahrenheit = document.getElementById('btn-fahrenheit');

    function celsiusToFahrenheit(celsius) {
        return Math.round((celsius * 9/5) + 32);
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

    async function fetchFullForecast(lat, lon) {
        try {
            const response = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
            if (!response.ok) throw new Error('Weather API failed');
            const data = await response.json();
            
            currentData = data.current;
            forecastData = data.forecast;

            // Remove skeletons
            document.querySelectorAll('.skeleton').forEach(el => {
                el.classList.remove('skeleton');
                el.classList.remove('skeleton-text');
                el.classList.remove('w-50');
                el.classList.remove('w-75');
                // if(el.tagName === 'H1' || el.tagName === 'H3' || el.tagName === 'P') el.textContent = ''; // Clear "Loading..." text
            });
            document.querySelectorAll('.skeleton-icon').forEach(el => el.classList.remove('skeleton-icon'));
            document.querySelectorAll('.skeleton-card').forEach(el => el.classList.remove('skeleton-card'));

            updateCurrentWeather(data.current);
            updateHourlyForecast(data.forecast, data.current.timezone);
            updateDailyForecast(data.forecast, data.current.timezone);
            
            // Re-run unit update to ensure new data respects current selection
            updateDisplayUnits();

        } catch (error) {
            console.error(error);
            if(cityEl) {
                cityEl.classList.remove('skeleton'); 
                cityEl.textContent = "Error loading weather";
            }
        }
    }

    function updateCurrentWeather(current) {
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
            
            // Map icons (Simplified)
            let iconClass = 'fa-sun';
            const id = w.id;
            if (id >= 200 && id < 300) iconClass = 'fa-bolt';
            else if (id >= 300 && id < 500) iconClass = 'fa-cloud-rain';
            else if (id >= 500 && id < 600) iconClass = 'fa-cloud-showers-heavy';
            else if (id >= 600 && id < 700) iconClass = 'fa-snowflake';
            else if (id >= 700 && id < 800) iconClass = 'fa-smog';
            else if (id === 800) iconClass = current.weather[0].icon.includes('n') ? 'fa-moon' : 'fa-sun';
            else if (id > 800) iconClass = 'fa-cloud';
            
            if(heroIconEl) heroIconEl.className = `fas ${iconClass} fa-4x mb-2`;
        }

        // Details
        if(windEl) windEl.textContent = `${current.wind.speed} m/s`;
        if(humidityEl) humidityEl.textContent = `${current.main.humidity}%`;
        
        if(maxTempEl) {
            const max = Math.round(current.main.temp_max);
            maxTempEl.setAttribute('data-celsius', max);
            maxTempEl.textContent = `${max}°`;
        }
        if(minTempEl) {
             const min = Math.round(current.main.temp_min);
             minTempEl.setAttribute('data-celsius', min);
             minTempEl.textContent = `${min}°`;
        }

        // Update Highlights Section
        if (highlightDateEl) {
            const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
            highlightDateEl.textContent = new Date().toLocaleDateString('en-US', options);
        }
        if (highlightMaxEl) {
            const max = Math.round(current.main.temp_max);
            highlightMaxEl.setAttribute('data-celsius', max);
            highlightMaxEl.textContent = `${max}°`;
        }
        if (highlightMinEl) {
            const min = Math.round(current.main.temp_min);
            highlightMinEl.setAttribute('data-celsius', min);
            highlightMinEl.textContent = `${min}°`;
        }
        if (highlightVariationEl) {
            const var_temp = Math.round(current.main.temp_max - current.main.temp_min);
            highlightVariationEl.setAttribute('data-celsius', var_temp);
            highlightVariationEl.textContent = `${var_temp}°`;
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
            const wId = item.weather[0].id;
             let iconClass = 'fa-sun';
            if (wId >= 300 && wId < 600) iconClass = 'fa-cloud-rain';
            else if (wId >= 600 && wId < 700) iconClass = 'fa-snowflake';
            else if (wId === 800) iconClass = item.weather[0].icon.includes('n') ? 'fa-moon' : 'fa-sun';
            else iconClass = 'fa-cloud';

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
            const wId = day.weather.id;
             let iconClass = 'fa-sun';
            if (wId >= 300 && wId < 600) iconClass = 'fa-cloud-rain';
            else if (wId >= 600 && wId < 700) iconClass = 'fa-snowflake';
            else if (wId === 800) iconClass = 'fa-sun';
            else iconClass = 'fa-cloud';

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
    // Get location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            fetchFullForecast(pos.coords.latitude, pos.coords.longitude);
        }, () => {
             // Default to London
            fetchFullForecast(51.505, -0.09);
        });
    } else {
        fetchFullForecast(51.505, -0.09);
    }
});
