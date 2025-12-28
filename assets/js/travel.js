
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('travel-search-input');
    const searchResults = document.getElementById('travel-search-results');
    const searchBtn = document.getElementById('travel-search-btn');
    const contentArea = document.getElementById('travel-content');
    
    // Config
    let currentDest = null;
    let currentLat = null;
    let currentLon = null;

    // init autocomplete
    if (window.AutocompleteUtils && searchInput) {
        window.AutocompleteUtils.initAutocomplete(searchInput, searchResults, (city) => {
            loadDestination(city.city, city.lat, city.lon, city.country);
        });
    }

    searchBtn.addEventListener('click', () => {
        const query = searchInput.value;
        if(query) {
            // Basic search if typed manually
            // We'll rely on the API to find it
            // This is a simplified fallback if they didn't click the dropdown
             fetch(`/api/travel/weather?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    if(data.error) alert(data.error);
                    else loadDestination(data.city, data.lat, data.lon, data.country);
                });
        }
    });

    async function loadDestination(city, lat, lon, country) {
        currentDest = city;
        currentLat = lat;
        currentLon = lon;
        
        // Show Content
        contentArea.style.display = 'block';
        contentArea.scrollIntoView({ behavior: 'smooth' });

        // Update Header
        document.getElementById('dest-name').textContent = city;
        document.getElementById('dest-country').textContent = country || '';

        // 1. Fetch Basic Weather
        fetchWeather(lat, lon);

        // 2. Fetch Currency Rates
        fetchCurrency();

        // 3. Fetch Packing List
        fetchPackingList(city);
        
        // 4. Fetch History for Chart
        fetchHistory(lat, lon);
    }

    async function fetchWeather(lat, lon) {
        try {
            const res = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            
            // Header Stats
            const temp = Math.round(data.current.main.temp);
            const condition = data.current.weather[0].description;
            const icon = data.current.weather[0].icon;
            
            document.getElementById('dest-temp').textContent = `${temp}°C`;
            document.getElementById('dest-condition').textContent = condition.charAt(0).toUpperCase() + condition.slice(1);
            document.getElementById('dest-icon').src = `https://openweathermap.org/img/wn/${icon}@2x.png`;
            
            // Render Forecast (Daily)
            const forecastEl = document.getElementById('travel-forecast');
            forecastEl.innerHTML = '<div class="d-flex overflow-auto gap-3 pb-2" id="forecast-scroll"></div>';
            const container = document.getElementById('forecast-scroll');

            // Simplified daily aggregate (similar to main weather.js logic)
            const daily = {};
            data.forecast.list.forEach(item => {
                const day = new Date(item.dt * 1000).toDateString();
                if(!daily[day]) {
                     daily[day] = item; // take first entry (often noonish if sequence is standard, or just first)
                }
            });
            
            Object.values(daily).slice(0, 5).forEach(day => {
                const date = new Date(day.dt * 1000);
                const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
                const iconCode = day.weather[0].icon;
                
                const div = document.createElement('div');
                div.className = 'card border-0 bg-light rounded-4 text-center p-3 animate-fade-in';
                div.style.minWidth = '120px';
                div.innerHTML = `
                    <div class="small fw-bold text-muted">${dayName}</div>
                    <img src="https://openweathermap.org/img/wn/${iconCode}.png" width="50" class="my-1">
                    <div class="fw-bold">${Math.round(day.main.temp)}°</div>
                    <div class="x-small text-muted">${day.weather[0].main}</div>
                `;
                container.appendChild(div);
            });

        } catch (e) {
            console.error("Weather fetch failed", e);
        }
    }

    async function fetchCurrency() {
        const base = document.getElementById('currency-base').value;
        const amount = document.getElementById('currency-amount').value || 100;
        const container = document.getElementById('currency-results');
        
        container.innerHTML = '<div class="placeholder-glow"><span class="placeholder col-12 rounded"></span></div>';

        try {
            // Get rates
            const res = await fetch(`/api/currency/convert?base=${base}`);
            const data = await res.json();
            
            container.innerHTML = '';
            
            Object.entries(data.rates).forEach(([currency, rate]) => {
                if(currency === base) return;
                
                const total = (rate * amount).toFixed(2);
                
                const row = document.createElement('div');
                row.className = 'd-flex justify-content-between align-items-center bg-light rounded px-3 py-2';
                row.innerHTML = `
                    <div class="small fw-bold text-secondary">${currency}</div>
                    <div class="fw-bold fs-5">${total}</div>
                `;
                container.appendChild(row);
            });

        } catch (e) {
            container.innerHTML = '<small class="text-danger">Failed to load rates</small>';
        }
    }

    // Currency Listeners
    document.getElementById('currency-amount').addEventListener('input', fetchCurrency);
    document.getElementById('currency-base').addEventListener('change', fetchCurrency);

    async function fetchPackingList(city) {
         const container = document.getElementById('packing-list');
         container.innerHTML = '<div class="text-center py-4"><div class="spinner-border spinner-border-sm text-white" role="status"></div></div>';
         
         // Get current summary from DOM (hacky but easy)
         const cond = document.getElementById('dest-condition').textContent;
         const temp = document.getElementById('dest-temp').textContent;
         
         const weatherSummary = `${cond}, ${temp}`;

         try {
             const res = await fetch(`/api/travel/packing-list?destination=${encodeURIComponent(city)}&weather=${encodeURIComponent(weatherSummary)}`);
             const data = await res.json();
             
             container.innerHTML = '';
             
             if(data.items && data.items.length > 0) {
                 data.items.forEach(item => {
                     const el = document.createElement('div');
                     el.className = 'd-flex align-items-center bg-white bg-opacity-25 rounded px-3 py-2 text-white';
                     el.style.backdropFilter = 'blur(5px)';
                     el.innerHTML = `
                        <i class="fas ${item.icon || 'fa-check'} me-2 opacity-75"></i>
                        <span>${item.item}</span>
                     `;
                     container.appendChild(el);
                 });
             } else {
                 container.innerHTML = '<div class="small text-white opacity-50 text-center">No suggestions</div>';
             }

         } catch (e) {
             container.innerHTML = '<div class="small text-white opacity-50 text-center">AI unavailable</div>';
         }
    }

    async function fetchHistory(lat, lon) {
        const ctx = document.getElementById('travelHistoryChart');
        if(!ctx) return;
        
        // Ideally we fetch actual history. Reusing the dummy endpoint or historical cache.
        // For simplicity in this demo task, I'll fetch `/api/weather/history` which might trigger a fresh cache fill.
        
        try {
            const res = await fetch(`/api/weather/history?lat=${lat}&lon=${lon}`);
            const data = await res.json();
            
            // Format for chart: Date vs Temp
            const labels = data.map(d => {
                const date = new Date(d.date);
                return date.getDate(); // Just day number
            });
            const temps = data.map(d => d.temp);
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Typical Temp (°C)',
                        data: temps,
                        borderColor: '#2c5364',
                        backgroundColor: 'rgba(44, 83, 100, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: {
                         x: { display: false },
                         y: { grid: { display: false } }
                    }
                }
            });

        } catch (e) {
            console.log("Chart load fail");
        }
    }
});
