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
            console.error(error);
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
        
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weathercode&hourly=temperature_2m,weathercode&timezone=auto`;
        
        try {
            const res = await fetch(weatherUrl);
            const data = await res.json();
            
            if (data.current) {
                if(tempEl) tempEl.textContent = `${Math.round(data.current.temperature_2m)}°`;
                if(windEl) windEl.textContent = `${data.current.wind_speed_10m} km/h`;
                if(humidityEl) humidityEl.textContent = `${data.current.relative_humidity_2m}%`;
                
                // Update time/date based on timezone
                const localTime = new Date(new Date().toLocaleString("en-US", {timeZone: data.timezone}));
                
                if(timeEl) timeEl.textContent = localTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
                if(dateEl) dateEl.textContent = localTime.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
                if(dayEl) dayEl.textContent = "Today"; 
            }

            if (data.hourly && forecastEl) {
                updateForecast(data.hourly, data.timezone);
            }

        } catch (error) {
            console.error("Weather error:", error);
            if(cityEl) cityEl.textContent = "Error";
        }
    }

    function updateForecast(hourly, timezone) {
        forecastEl.innerHTML = '';
        
        // Get current time in the city's timezone
        const cityTime = new Date(new Date().toLocaleString("en-US", {timeZone: timezone}));
        
        const year = cityTime.getFullYear();
        const month = String(cityTime.getMonth() + 1).padStart(2, '0');
        const day = String(cityTime.getDate()).padStart(2, '0');
        const hour = String(cityTime.getHours()).padStart(2, '0');
        
        const currentHourStr = `${year}-${month}-${day}T${hour}:00`;
        
        let startIndex = hourly.time.indexOf(currentHourStr);
        // If exact match not found (e.g. API delay), try to find closest
        if (startIndex === -1) {
             startIndex = hourly.time.findIndex(t => t >= currentHourStr);
             if (startIndex === -1) startIndex = 0;
        }

        // Show next 5 items (e.g. current + 4 intervals)
        for (let i = 0; i < 5; i++) {
            const index = startIndex + (i * 3); // Every 3 hours
            if (index >= hourly.time.length) break;

            const temp = Math.round(hourly.temperature_2m[index]);
            const timeStr = hourly.time[index].split('T')[1]; // HH:MM
            const wCode = hourly.weathercode[index];
            
            // Map weather code to icon
            let iconClass = 'fa-sun';
            if (wCode > 3) iconClass = 'fa-cloud';
            if (wCode > 45) iconClass = 'fa-smog';
            if (wCode > 50) iconClass = 'fa-cloud-rain';
            if (wCode > 60) iconClass = 'fa-cloud-showers-heavy';
            if (wCode > 70) iconClass = 'fa-snowflake';
            if (wCode > 95) iconClass = 'fa-bolt';

            const div = document.createElement('div');
            div.className = i === 0 ? 'bg-primary text-white rounded-3 py-4 d-flex flex-column align-items-center justify-content-center forecast-card-hover' : 'bg-light text-primary rounded-3 py-4 d-flex flex-column align-items-center justify-content-center forecast-card-hover';
            div.style.minWidth = '55px';
            
            div.innerHTML = `
                <p class="small mb-1" style="font-size: 10px;">${i === 0 ? 'Now' : timeStr}</p>
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
