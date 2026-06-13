document.addEventListener('DOMContentLoaded', function() {
    // State variables
    let currentData = null;
    let forecastData = null;
    let pollutionData = null;
    let currentUnit = 'C'; // Celsius by default
    let activeTab = '24h'; // '24h' or '7d'
    let currentPeriodOffset = 0; // scroll offset for forecast periods

    // UI Elements
    const locationTextEl = document.getElementById('location-text');
    const refreshTimeEl = document.getElementById('refresh-time');
    const currentTempEl = document.getElementById('current-temp');
    const searchInput = document.getElementById('dashboard-search-input');
    const searchResults = document.getElementById('dashboard-search-results');
    const targetIcon = document.getElementById('target-location');
    const refreshIcon = document.getElementById('refresh-icon');

    // Units toggle
    const btnCelsius = document.getElementById('btn-celsius-dash');
    const btnFahrenheit = document.getElementById('btn-fahrenheit-dash');

    // Forecast Tabs
    const tab24h = document.getElementById('tab-24h');
    const tab7d = document.getElementById('tab-7d');
    const forecastCardsContainer = document.getElementById('forecast-cards');

    // Navigation buttons
    const btnPrevPeriod = document.getElementById('btn-prev-period');
    const btnNextPeriod = document.getElementById('btn-next-period');

    // Autocomplete for search
    if (searchInput && searchResults) {
        AutocompleteUtils.initAutocomplete(searchInput, searchResults, (city) => {
            fetchDashboardWeather(city.lat, city.lon, city.display_name);
        });
    }

    // Geolocation target button
    if (targetIcon) {
        targetIcon.addEventListener('click', () => {
            getUserLocation();
        });
    }

    // Refresh button
    if (refreshIcon) {
        refreshIcon.addEventListener('click', () => {
            if (currentData) {
                fetchDashboardWeather(currentData.coord.lat, currentData.coord.lon, locationTextEl.textContent);
            } else {
                getUserLocation();
            }
        });
    }

    // Temperature Unit toggle listeners
    if (btnCelsius && btnFahrenheit) {
        btnCelsius.addEventListener('click', () => {
            if (currentUnit !== 'C') {
                currentUnit = 'C';
                btnCelsius.classList.add('active');
                btnFahrenheit.classList.remove('active');
                updateTemperatureDisplays();
            }
        });

        btnFahrenheit.addEventListener('click', () => {
            if (currentUnit !== 'F') {
                currentUnit = 'F';
                btnFahrenheit.classList.add('active');
                btnCelsius.classList.remove('active');
                updateTemperatureDisplays();
            }
        });
    }

    // Forecast Tab listeners
    if (tab24h && tab7d) {
        tab24h.addEventListener('click', () => {
            if (activeTab !== '24h') {
                activeTab = '24h';
                tab24h.classList.add('active');
                tab7d.classList.remove('active');
                renderForecast();
            }
        });

        tab7d.addEventListener('click', () => {
            if (activeTab !== '7d') {
                activeTab = '7d';
                tab7d.classList.add('active');
                tab24h.classList.remove('active');
                renderForecast();
            }
        });
    }

    // Period Navigation listeners
    if (btnPrevPeriod && btnNextPeriod) {
        btnPrevPeriod.addEventListener('click', () => {
            if (activeTab === '24h' && currentPeriodOffset > 0) {
                currentPeriodOffset--;
                renderForecast();
            }
        });

        btnNextPeriod.addEventListener('click', () => {
            if (activeTab === '24h' && currentPeriodOffset < 1) { // Max offset is 1 since we have 4 periods and show 3
                currentPeriodOffset++;
                renderForecast();
            }
        });
    }

    // Get location
    function getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                async (position) => {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    
                    // Call Reverse Geocode
                    try {
                        const res = await fetch(`/api/geocode/reverse?lat=${lat}&lon=${lon}`);
                        if (res.ok) {
                            const geocode = await res.json();
                            const address = geocode.address;
                            const formatted = formatDetailedAddress(address);
                            fetchDashboardWeather(lat, lon, formatted);
                        } else {
                            fetchDashboardWeather(lat, lon, "My Location");
                        }
                    } catch (e) {
                        fetchDashboardWeather(lat, lon, "My Location");
                    }
                },
                (error) => {
                    console.warn("Geolocation failed, using IP fallback", error);
                    getIPLocation();
                }
            );
        } else {
            getIPLocation();
        }
    }

    async function getIPLocation() {
        try {
            const res = await fetch('/api/ip-location');
            if (res.ok) {
                const ipLoc = await res.json();
                if (ipLoc.status !== 'fail') {
                    const formatted = `${ipLoc.city}, ${ipLoc.countryCode}`;
                    fetchDashboardWeather(ipLoc.lat, ipLoc.lon, formatted);
                } else {
                    useDefaultLocation();
                }
            } else {
                useDefaultLocation();
            }
        } catch (e) {
            useDefaultLocation();
        }
    }

    function useDefaultLocation() {
        // Fallback: Islamabad, Pakistan
        fetchDashboardWeather(33.6844, 73.0479, "Sector I-10, Islamabad, Pakistan");
    }

    function formatDetailedAddress(address) {
        if (!address) return "Sector I-10, Islamabad, Pakistan";
        const parts = [];
        
        // Build address string similar to: "734 street 3 i 10/2 i 10 islamabad..."
        if (address.house_number) parts.push(address.house_number);
        if (address.road) parts.push(address.road);
        if (address.suburb) parts.push(address.suburb);
        if (address.neighbourhood && address.neighbourhood !== address.suburb) {
            parts.push(address.neighbourhood);
        }
        if (address.city || address.town || address.village) {
            parts.push(address.city || address.town || address.village);
        }
        
        let formatted = parts.join(' ');
        if (!formatted) formatted = address.display_name;
        
        // Truncate if too long and add ellipsis
        if (formatted.length > 45) {
            formatted = formatted.substring(0, 42) + '...';
        }
        return formatted;
    }

    // Fetch weather data
    async function fetchDashboardWeather(lat, lon, name) {
        if (locationTextEl) locationTextEl.textContent = "Loading location...";
        
        try {
            let translatedName = name;
            if (/[a-zA-Z]/.test(name)) {
                try {
                    const transRes = await fetch(`/api/translate/address?text=${encodeURIComponent(name)}`);
                    if (transRes.ok) {
                        const transData = await transRes.json();
                        if (transData.translated) {
                            translatedName = transData.translated;
                        }
                    }
                } catch (e) {
                    console.warn("Translation failed:", e);
                }
            }

            const res = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
            if (!res.ok) throw new Error("Weather API error");
            const data = await res.json();
            
            // Cache data
            data.cityName = translatedName;
            localStorage.setItem('synocast_weather_cache', JSON.stringify(data));
            
            currentData = data.current;
            forecastData = data.forecast;
            pollutionData = data.pollution;
            
            // Render UI
            if (locationTextEl) locationTextEl.textContent = translatedName;
            renderDashboard();

            // Cache and dispatch location to update top navbar and other pages
            const locData = { lat, lon, timestamp: new Date().getTime() };
            localStorage.setItem('synocast_cached_location', JSON.stringify(locData));
            localStorage.setItem('synocast_permission_hint', 'true');
            sessionStorage.setItem('synocast_location_fixed', 'true');
            
            window.synocast_current_loc = { lat, lon, isCached: false };
            
            window.dispatchEvent(new CustomEvent('synocast_location_granted', {
                detail: window.synocast_current_loc
            }));
        } catch (err) {
            console.error("Dashboard fetch error", err);
            if (locationTextEl) locationTextEl.textContent = "Error loading weather data";
        }
    }

    function formatDateTime(localDate) {
        const hours = localDate.getHours();
        const minutes = localDate.getMinutes();
        const ampm = hours >= 12 ? 'pm' : 'am';
        const displayHours = hours % 12 || 12;
        const displayMinutes = minutes < 10 ? '0' + minutes : minutes;
        
        const month = localDate.toLocaleDateString('en-US', { month: 'short' });
        const day = localDate.getDate();
        
        let suffix = 'th';
        if (day === 1 || day === 21 || day === 31) suffix = 'st';
        else if (day === 2 || day === 22) suffix = 'nd';
        else if (day === 3 || day === 23) suffix = 'rd';
        
        return `${displayHours}:${displayMinutes} ${ampm} , ${month} ${day}${suffix}`;
    }

    function renderDashboard() {
        if (!currentData) return;

        // 1. Time display
        const offsetSeconds = currentData.timezone; 
        const localDate = new Date(new Date().getTime() + (offsetSeconds * 1000) + (new Date().getTimezoneOffset() * 60000));
        if (refreshTimeEl) refreshTimeEl.textContent = formatDateTime(localDate);

        // 2. Large Temperature
        updateLargeTemperature();

        // 3. Grid Metrics
        renderGridMetrics();

        // 4. Forecast Section
        renderForecast();
    }

    function updateLargeTemperature() {
        if (!currentTempEl || !currentData) return;
        const tempC = Math.round(currentData.main.temp * 10) / 10;
        
        if (currentUnit === 'F') {
            const tempF = Math.round(WeatherUtils.celsiusToFahrenheit(tempC) * 10) / 10;
            currentTempEl.innerHTML = `${tempF}<span class="unit">°F</span>`;
        } else {
            currentTempEl.innerHTML = `${tempC.toFixed(1)}<span class="unit">°C</span>`;
        }
    }

    function updateTemperatureDisplays() {
        updateLargeTemperature();
        renderGridMetrics();
        renderForecast();
    }

    function renderGridMetrics() {
        if (!currentData) return;

        // 1. Wind Speed
        const speedMS = currentData.wind.speed;
        const speedKmH = Math.round(speedMS * 3.6 * 10) / 10;
        const windValEl = document.getElementById('metric-wind-val');
        if (windValEl) windValEl.textContent = `${speedKmH.toFixed(1)} Km/h`;

        // 2. PAK AQI
        const aqiValEl = document.getElementById('metric-aqi-val');
        const aqiSubEl = document.getElementById('metric-aqi-sub');
        if (pollutionData && pollutionData.list && pollutionData.list[0]) {
            const aqiLevel = pollutionData.list[0].main.aqi; // 1-5
            const aqiMap = {
                1: { val: 24, label: "Good" },
                2: { val: 72, label: "Fair" },
                3: { val: 103, label: "Moderate" },
                4: { val: 156, label: "Poor" },
                5: { val: 245, label: "Very Poor" }
            };
            const mapped = aqiMap[aqiLevel] || { val: 103, label: "Moderate" };
            if (aqiValEl) aqiValEl.textContent = mapped.val;
            if (aqiSubEl) aqiSubEl.textContent = mapped.label;
        } else {
            if (aqiValEl) aqiValEl.textContent = "103";
            if (aqiSubEl) aqiSubEl.textContent = "Moderate";
        }

        // 3. Rain Chances
        let rainChance = 0;
        if (forecastData && forecastData.list) {
            // Find rain chance (pop) in the current hour's forecast chunk
            rainChance = Math.round((forecastData.list[0].pop || 0) * 100);
        }
        const rainValEl = document.getElementById('metric-rain-val');
        if (rainValEl) rainValEl.textContent = `${rainChance} %`;

        // 4. Humidity
        const humidity = currentData.main.humidity;
        const humidityValEl = document.getElementById('metric-humidity-val');
        if (humidityValEl) humidityValEl.textContent = `${humidity} %`;

        // 5. UV Index
        const offsetSeconds = currentData.timezone; 
        const localDate = new Date(new Date().getTime() + (offsetSeconds * 1000) + (new Date().getTimezoneOffset() * 60000));
        const uvIndex = estimateUV(currentData.clouds.all, currentData.sys.sunset, currentData.sys.sunrise, localDate);
        const uvValEl = document.getElementById('metric-uv-val');
        if (uvValEl) uvValEl.textContent = uvIndex;

        // 6. Temperature min/max range
        const maxTempEl = document.getElementById('metric-temp-max');
        const minTempEl = document.getElementById('metric-temp-min');
        
        let maxTempC = currentData.main.temp_max;
        let minTempC = currentData.main.temp_min;
        
        if (forecastData && forecastData.list) {
            // Scan next 24h (8 chunks of 3 hours)
            const chunks = forecastData.list.slice(0, 8);
            maxTempC = Math.max(...chunks.map(c => c.main.temp_max));
            minTempC = Math.min(...chunks.map(c => c.main.temp_min));
        }

        if (currentUnit === 'F') {
            const maxF = Math.round(WeatherUtils.celsiusToFahrenheit(maxTempC) * 10) / 10;
            const minF = Math.round(WeatherUtils.celsiusToFahrenheit(minTempC) * 10) / 10;
            if (maxTempEl) maxTempEl.innerHTML = `↑ ${maxF.toFixed(1)} °F`;
            if (minTempEl) minTempEl.innerHTML = `↓ ${minF.toFixed(1)} °F`;
        } else {
            if (maxTempEl) maxTempEl.innerHTML = `↑ ${maxTempC.toFixed(1)} °C`;
            if (minTempEl) minTempEl.innerHTML = `↓ ${minTempC.toFixed(1)} °C`;
        }
    }

    function estimateUV(cloudsPercent, sunsetTime, sunriseTime, localTime) {
        const hour = localTime.getHours();
        if (hour < 5 || hour > 19) return 0;
        
        const distanceFromPeak = Math.abs(12.5 - hour);
        let baseUV = Math.max(0, 10 - distanceFromPeak * 1.6); // Peak is 10
        baseUV = baseUV * (1 - (cloudsPercent / 100) * 0.65);
        return Math.max(0, Math.round(baseUV));
    }

    function renderForecast() {
        if (!forecastData || !forecastCardsContainer) return;

        forecastCardsContainer.innerHTML = '';

        if (activeTab === '24h') {
            const periods = aggregate24HourPeriods();
            
            // Show 3 periods starting from currentPeriodOffset
            const visiblePeriods = periods.slice(currentPeriodOffset, currentPeriodOffset + 3);

            // Update arrow button active states
            if (btnPrevPeriod) btnPrevPeriod.disabled = currentPeriodOffset === 0;
            if (btnNextPeriod) btnNextPeriod.disabled = currentPeriodOffset >= periods.length - 3;

            visiblePeriods.forEach(p => {
                const card = document.createElement('div');
                card.className = 'glass-panel forecast-period-card init-fade-in';
                
                const highTemp = currentUnit === 'F' ? Math.round(WeatherUtils.celsiusToFahrenheit(p.high)) : Math.round(p.high);
                const lowTemp = currentUnit === 'F' ? Math.round(WeatherUtils.celsiusToFahrenheit(p.low)) : Math.round(p.low);

                card.innerHTML = `
                    <div>
                        <h6 class="period-title">${p.title}</h6>
                        <div class="period-divider"></div>
                        <div class="period-content">
                            <div class="period-icon-container">
                                <i class="fa-solid ${p.iconClass}"></i>
                            </div>
                            <div class="period-details">
                                <div class="period-time">${p.timeRange}</div>
                                <div class="period-temp-range">
                                    ↑ High: ${highTemp}° ↓ Low: ${lowTemp}°
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="period-divider"></div>
                        <p class="period-summary">${p.summary}</p>
                    </div>
                `;
                forecastCardsContainer.appendChild(card);
            });
        } else {
            // 7 Days Daily Forecast
            const dailyData = aggregate7DaysForecast();
            
            if (btnPrevPeriod) btnPrevPeriod.disabled = true;
            if (btnNextPeriod) btnNextPeriod.disabled = true;

            dailyData.forEach((day, index) => {
                const card = document.createElement('div');
                card.className = 'glass-panel forecast-period-card init-fade-in';
                card.style.animationDelay = `${index * 0.05}s`;
                
                const highTemp = currentUnit === 'F' ? Math.round(WeatherUtils.celsiusToFahrenheit(day.high)) : Math.round(day.high);
                const lowTemp = currentUnit === 'F' ? Math.round(WeatherUtils.celsiusToFahrenheit(day.low)) : Math.round(day.low);

                card.innerHTML = `
                    <div>
                        <h6 class="period-title">${day.dayName}</h6>
                        <div class="period-divider"></div>
                        <div class="period-content">
                            <div class="period-icon-container">
                                <i class="fa-solid ${day.iconClass}"></i>
                            </div>
                            <div class="period-details">
                                <div class="period-time">${day.dateString}</div>
                                <div class="period-temp-range">
                                    High: ${highTemp}° / Low: ${lowTemp}°
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div class="period-divider"></div>
                        <p class="period-summary">${day.condition} (${day.rainChance}% rain chance)</p>
                    </div>
                `;
                forecastCardsContainer.appendChild(card);
            });
        }
    }

    function aggregate24HourPeriods() {
        if (!forecastData || !forecastData.list) return [];

        const list = forecastData.list;
        const timezoneOffset = currentData.timezone;

        // Group into periods:
        // Night to Morning (12 AM - 6 AM or 4 AM - 6 AM in reference)
        // Morning to Noon (6 AM - 12 PM)
        // Noon to Evening (12 PM - 6 PM)
        // Evening to Night (6 PM - 12 AM)
        const periodsConfig = [
            { id: 'night', title: 'Night to Morning', startHour: 0, endHour: 6, label: '4 AM to 6 AM' },
            { id: 'morning', title: 'Morning to Noon', startHour: 6, endHour: 12, label: '6 AM to 12 PM' },
            { id: 'noon', title: 'Noon to Evening', startHour: 12, endHour: 18, label: '12 PM to 6 PM' },
            { id: 'evening', title: 'Evening to Night', startHour: 18, endHour: 24, label: '6 PM to 12 AM' }
        ];

        const periods = [];

        periodsConfig.forEach(config => {
            const periodItems = list.filter(item => {
                const date = new Date(item.dt * 1000);
                const localDate = new Date(date.getTime() + (timezoneOffset * 1000) + (date.getTimezoneOffset() * 60000));
                const hour = localDate.getHours();
                return hour >= config.startHour && hour < config.endHour;
            });

            if (periodItems.length > 0) {
                const temps = periodItems.map(item => item.main.temp);
                const high = Math.max(...temps);
                const low = Math.min(...temps);
                const maxPop = Math.max(...periodItems.map(item => item.pop || 0));
                const firstItem = periodItems[0];
                const weatherId = firstItem.weather[0].id;
                const weatherIcon = firstItem.weather[0].icon;
                const iconMeta = WeatherUtils.getIconClass(weatherId, weatherIcon);

                let summary = "Weather to remain partly cloudy during these hours.";
                if (maxPop > 0.25) {
                    summary = `${Math.round(maxPop * 100)}% chance of rain during these hours.`;
                } else {
                    const desc = firstItem.weather[0].description.toLowerCase();
                    if (desc.includes('clear')) {
                        summary = "Weather to remain clear during these hours.";
                    } else if (desc.includes('cloud')) {
                        summary = "Weather to remain partly cloudy during these hours.";
                    } else if (desc.includes('rain') || desc.includes('drizzle')) {
                        summary = "Light showers expected during these hours.";
                    } else if (desc.includes('snow')) {
                        summary = "Snowfall expected during these hours.";
                    } else if (desc.includes('storm')) {
                        summary = "Stormy weather expected during these hours.";
                    }
                }

                periods.push({
                    title: config.title,
                    timeRange: config.label,
                    high: high,
                    low: low,
                    iconClass: iconMeta.icon,
                    summary: summary
                });
            } else {
                // If current day periods are past, show next day's periods
                const configItems = list.slice(0, 16); // Look slightly ahead
                const futurePeriodItems = configItems.filter(item => {
                    const date = new Date(item.dt * 1000);
                    const localDate = new Date(date.getTime() + (timezoneOffset * 1000) + (date.getTimezoneOffset() * 60000));
                    const hour = localDate.getHours();
                    return hour >= config.startHour && hour < config.endHour;
                });

                if (futurePeriodItems.length > 0) {
                    const temps = futurePeriodItems.map(item => item.main.temp);
                    const high = Math.max(...temps);
                    const low = Math.min(...temps);
                    const maxPop = Math.max(...futurePeriodItems.map(item => item.pop || 0));
                    const firstItem = futurePeriodItems[0];
                    const weatherId = firstItem.weather[0].id;
                    const weatherIcon = firstItem.weather[0].icon;
                    const iconMeta = WeatherUtils.getIconClass(weatherId, weatherIcon);

                    let summary = "Weather to remain partly cloudy during these hours.";
                    if (maxPop > 0.25) {
                        summary = `${Math.round(maxPop * 100)}% chance of rain during these hours.`;
                    } else {
                        const desc = firstItem.weather[0].description.toLowerCase();
                        if (desc.includes('clear')) {
                            summary = "Weather to remain clear during these hours.";
                        } else if (desc.includes('cloud')) {
                            summary = "Weather to remain partly cloudy during these hours.";
                        }
                    }

                    periods.push({
                        title: config.title,
                        timeRange: config.label,
                        high: high,
                        low: low,
                        iconClass: iconMeta.icon,
                        summary: summary
                    });
                }
            }
        });

        // Ensure we always have at least 3 periods to show
        return periods;
    }

    function aggregate7DaysForecast() {
        if (!forecastData || !forecastData.list) return [];

        const list = forecastData.list;
        const timezoneOffset = currentData.timezone;

        // Group by day key
        const daysGroup = {};

        list.forEach(item => {
            const date = new Date(item.dt * 1000);
            const localDate = new Date(date.getTime() + (timezoneOffset * 1000) + (date.getTimezoneOffset() * 60000));
            const dayKey = localDate.toDateString(); // e.g. "Sat Jun 13 2026"

            if (!daysGroup[dayKey]) {
                daysGroup[dayKey] = {
                    dayName: localDate.toLocaleDateString('en-US', { weekday: 'long' }),
                    dateString: localDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                    temps: [item.main.temp],
                    pois: [item.pop || 0],
                    weathers: [item.weather[0]]
                };
            } else {
                daysGroup[dayKey].temps.push(item.main.temp);
                daysGroup[dayKey].pois.push(item.pop || 0);
                daysGroup[dayKey].weathers.push(item.weather[0]);
            }
        });

        const distinctDays = Object.values(daysGroup).slice(0, 7);

        return distinctDays.map(d => {
            const high = Math.max(...d.temps);
            const low = Math.min(...d.temps);
            const rainChance = Math.round(Math.max(...d.pois) * 100);
            
            // Find most frequent weather condition
            const count = {};
            let mostFreq = d.weathers[0];
            let maxCount = 0;
            d.weathers.forEach(w => {
                count[w.id] = (count[w.id] || 0) + 1;
                if (count[w.id] > maxCount) {
                    maxCount = count[w.id];
                    mostFreq = w;
                }
            });

            const iconMeta = WeatherUtils.getIconClass(mostFreq.id, mostFreq.icon);

            return {
                dayName: d.dayName,
                dateString: d.dateString,
                high: high,
                low: low,
                rainChance: rainChance,
                iconClass: iconMeta.icon,
                condition: mostFreq.main
            };
        });
    }

    // Initialize Page
    const cache = JSON.parse(localStorage.getItem('synocast_weather_cache'));
    if (cache) {
        currentData = cache.current;
        forecastData = cache.forecast;
        pollutionData = cache.pollution;
        locationTextEl.textContent = cache.cityName || currentData.name;
        renderDashboard();
        
        // Refresh silently in background
        if (currentData) {
            fetchDashboardWeather(currentData.coord.lat, currentData.coord.lon, locationTextEl.textContent);
        }
    } else {
        getUserLocation();
    }
});
