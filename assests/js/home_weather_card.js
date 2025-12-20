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

    async function addFavorite() {
        const query = newCityInput.value.trim();
        if (!query) return;

        // Show loading state on button
        let originalBtnHtml = '';
        if (addCityBtn) {
            originalBtnHtml = addCityBtn.innerHTML;
            addCityBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            addCityBtn.disabled = true;
        }

        try {
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;
            const res = await fetch(url);
            const data = await res.json();

            if (data && data.length > 0) {
                const city = {
                    name: data[0].display_name.split(',')[0], // Simple name
                    lat: data[0].lat,
                    lon: data[0].lon
                };
                
                // Check if already exists
                if (!favorites.some(f => f.name === city.name)) {
                    favorites.push(city);
                    localStorage.setItem('weatherFavorites', JSON.stringify(favorites));
                    renderFavorites();
                    newCityInput.value = '';
                } else {
                    alert('City already in favorites');
                }
            } else {
                alert('City not found');
            }
        } catch (error) {
            alert('Error searching for city');
        } finally {
            if (addCityBtn) {
                addCityBtn.innerHTML = originalBtnHtml;
                addCityBtn.disabled = false;
            }
        }
    }

    if(addCityBtn) {
        addCityBtn.addEventListener('click', addFavorite);
    }
    
    if(newCityInput) {
        newCityInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addFavorite();
        });
        // Prevent dropdown from closing when clicking input
        newCityInput.addEventListener('click', (e) => e.stopPropagation());
    }

    async function fetchWeather(lat, lon, cityName) {
        if(cityEl) cityEl.textContent = cityName || "Loading...";
        
        const weatherUrl = `/api/weather?lat=${lat}&lon=${lon}`;
        
        try {
            const res = await fetch(weatherUrl);
            const data = await res.json();
            
            if (data.current) {
                // Current Weather Data Mapping (OpenWeatherMap)
                if(tempEl) tempEl.textContent = `${Math.round(data.current.main.temp)}°`;
                if(windEl) windEl.textContent = `${data.current.wind.speed} m/s`; // OpenWeatherMap returns m/s by default
                if(humidityEl) humidityEl.textContent = `${data.current.main.humidity}%`;
                
                // Update time/date (using system time for now as OWM doesn't give simple timezone string like 'Europe/London')
                // But we can use the 'timezone' offset in seconds from OWM
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
            if(cityEl) cityEl.textContent = "Error";
        }
    }

    function updateForecast(forecastData, timezoneOffset) {
        forecastEl.innerHTML = '';
        
        // OpenWeatherMap 5-day forecast returns a list of 40 items (every 3 hours)
        const hourlyList = forecastData.list;
        
        // Show next 5 items from the list
        for (let i = 0; i < 5; i++) {
            if (i >= hourlyList.length) break;
            
            const item = hourlyList[i];
            const temp = Math.round(item.main.temp);
            
            // Calculate time for this forecast item
            // item.dt is unix timestamp
            const date = new Date(item.dt * 1000);
            // Adjust to city timezone if critical, but for simple display local browser time of the timestamp is usually fine 
            // or we shift it like we did for current time.
            // Let's keep it simple and show the time from the timestamp (which is UTC) converted to local or city time.
            // To match the city time logic properly:
            const itemTime = new Date(date.getTime() + (timezoneOffset * 1000) + (date.getTimezoneOffset() * 60000));
            
            const timeStr = itemTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

            const wCode = item.weather[0].id;
            
            // Map weather code to icon (OpenWeatherMap codes)
            let iconClass = 'fa-sun';
            if (wCode >= 200 && wCode < 300) iconClass = 'fa-bolt';
            else if (wCode >= 300 && wCode < 500) iconClass = 'fa-cloud-rain';
            else if (wCode >= 500 && wCode < 600) iconClass = 'fa-cloud-showers-heavy';
            else if (wCode >= 600 && wCode < 700) iconClass = 'fa-snowflake';
            else if (wCode >= 700 && wCode < 800) iconClass = 'fa-smog';
            else if (wCode === 800) iconClass = 'fa-sun';
            else if (wCode > 800) iconClass = 'fa-cloud';


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

    function getCurrentLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(async position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                // Get city name
                const geoUrl = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`;
                try {
                    const res = await fetch(geoUrl);
                    const data = await res.json();
                    const name = data.address.city || data.address.town || data.address.village || "My Location";
                    fetchWeather(lat, lon, name);
                } catch (e) {
                    fetchWeather(lat, lon, "My Location");
                }
            }, () => {
                // Default to London if denied
                fetchWeather(51.505, -0.09, "London");
            });
        } else {
            fetchWeather(51.505, -0.09, "London");
        }
    }

    // Initialize
    renderFavorites();
    getCurrentLocation();
});
