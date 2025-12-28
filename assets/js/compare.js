
document.addEventListener('DOMContentLoaded', () => {

    const input1 = document.getElementById('city1-input');
    const list1 = document.getElementById('city1-results');
    const input2 = document.getElementById('city2-input');
    const list2 = document.getElementById('city2-results');
    const compareBtn = document.getElementById('compare-btn');
    const swapBtn = document.getElementById('swap-btn');
    const view = document.getElementById('comparison-view');

    // State
    let city1 = null; // {lat, lon, name}
    let city2 = null;

    // Autocomplete
    if (window.AutocompleteUtils) {
        window.AutocompleteUtils.initAutocomplete(input1, list1, (c) => { 
            city1 = c; 
            input1.value = c.city;
        });
        window.AutocompleteUtils.initAutocomplete(input2, list2, (c) => { 
            city2 = c; 
            input2.value = c.city;
        });
    }

    swapBtn.addEventListener('click', () => {
        // Swap UI
        const tempVal = input1.value;
        input1.value = input2.value;
        input2.value = tempVal;
        
        // Swap Data
        const tempObj = city1;
        city1 = city2;
        city2 = tempObj;
        
        // Re-run if visible
        if(view.style.display !== 'none') compareBtn.click();
    });

    compareBtn.addEventListener('click', async () => {
        // Auto-resolve if text entered but no dropdown selected
        if (!city1 && input1.value.trim()) {
            city1 = await resolveCity(input1.value.trim());
        }
        if (!city2 && input2.value.trim()) {
            city2 = await resolveCity(input2.value.trim());
        }

        if(!city1 || !city2) {
             if(!city1) alert("Please select City 1 from the suggestions or check spelling.");
             else if(!city2) alert("Please select City 2 from the suggestions or check spelling.");
             return;
        }

        // Helper to resolve city
        async function resolveCity(name) {
            // 1. Try Local Dataset in AutocompleteUtils
            if (window.AutocompleteUtils && window.AutocompleteUtils.CITY_DATASET) {
                const match = window.AutocompleteUtils.CITY_DATASET.find(c => c.name.toLowerCase() === name.toLowerCase());
                if (match) {
                    return {
                        lat: match.lat,
                        lon: match.lon,
                        name: match.name, // Ensure consistency
                        display_name: `${match.name}, ${match.country}`,
                        city: match.name // Add this for consistency with autocomplete util output
                    };
                }
            }

            // 2. Try API
            try {
                const res = await fetch(`/api/geocode/search?q=${encodeURIComponent(name)}`);
                const data = await res.json();
                if (data && data.length > 0) {
                     const first = data[0];
                     return {
                         lat: first.lat,
                         lon: first.lon,
                         name: first.name,
                         display_name: first.display_name,
                         city: first.name
                     };
                }
            } catch (e) {
                console.error("Resolution error:", e);
            }
            return null;
        }

        view.style.display = 'block';
        view.scrollIntoView({ behavior: 'smooth' });
        
        // Fetch Parallel
        try {
            const [r1, r2] = await Promise.all([
                fetch(`/api/weather?lat=${city1.lat}&lon=${city1.lon}`),
                fetch(`/api/weather?lat=${city2.lat}&lon=${city2.lon}`)
            ]);
            
            const d1 = await r1.json();
            const d2 = await r2.json();
            
            renderCity('c1', d1);
            renderCity('c2', d2);
            
            generateSummary(d1, d2);

        } catch (e) {
            console.error(e);
            alert("Failed to compare data.");
        }
    });

    function renderCity(prefix, data) {
        const c = data.current;
        document.getElementById(`${prefix}-name`).textContent = c.name;
        document.getElementById(`${prefix}-country`).textContent = c.sys.country;
        document.getElementById(`${prefix}-temp`).textContent = `${Math.round(c.main.temp)}°`;
        document.getElementById(`${prefix}-cond`).textContent = c.weather[0].description;
        document.getElementById(`${prefix}-icon`).src = `https://openweathermap.org/img/wn/${c.weather[0].icon}@2x.png`;
        document.getElementById(`${prefix}-wind`).textContent = c.wind.speed;
        document.getElementById(`${prefix}-hum`).textContent = c.main.humidity;
    }

    function generateSummary(d1, d2) {
        const t1 = d1.current.main.temp;
        const t2 = d2.current.main.temp;
        const diff = Math.abs(t1 - t2).toFixed(1);
        
        let msg = `${d1.current.name} is `;
        
        if (Math.abs(t1 - t2) < 1) {
            msg += `about the same temperature as ${d2.current.name}.`;
        } else if (t1 > t2) {
            msg += `${diff}°C warmer than ${d2.current.name}.`;
        } else {
            msg += `${diff}°C colder than ${d2.current.name}.`;
        }
        
        // Add condition context
        msg += ` ${d1.current.name} is experiencing ${d1.current.weather[0].description}, while ${d2.current.name} has ${d2.current.weather[0].description}.`;
        
        document.getElementById('comparison-summary').textContent = msg;
    }
});
