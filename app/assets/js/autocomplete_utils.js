/**
 * AutocompleteUtils - A reusable utility for city name autocomplete.
 */
const AutocompleteUtils = {
    CITY_DATASET: [
        { name: "New York", country: "US", lat: 40.7128, lon: -74.0060 },
        { name: "London", country: "GB", lat: 51.5074, lon: -0.1278 },
        { name: "Tokyo", country: "JP", lat: 35.6895, lon: 139.6917 },
        { name: "Paris", country: "FR", lat: 48.8566, lon: 2.3522 },
        { name: "Dubai", country: "AE", lat: 25.2048, lon: 55.2708 },
        { name: "Singapore", country: "SG", lat: 1.3521, lon: 103.8198 },
        { name: "Sydney", country: "AU", lat: -33.8688, lon: 151.2093 },
        { name: "Berlin", country: "DE", lat: 52.5200, lon: 13.4050 },
        { name: "Toronto", country: "CA", lat: 43.6532, lon: -79.3832 },
        { name: "Mumbai", country: "IN", lat: 19.0760, lon: 72.8777 },
        { name: "Beijing", country: "CN", lat: 39.9042, lon: 116.4074 },
        { name: "Moscow", country: "RU", lat: 55.7558, lon: 37.6173 },
        { name: "Rome", country: "IT", lat: 41.9028, lon: 12.4964 },
        { name: "Madrid", country: "ES", lat: 40.4168, lon: -3.7038 },
        { name: "Amsterdam", country: "NL", lat: 52.3676, lon: 4.9041 },
        { name: "Seoul", country: "KR", lat: 37.5665, lon: 126.9780 },
        { name: "Bangkok", country: "TH", lat: 13.7563, lon: 100.5018 },
        { name: "Istanbul", country: "TR", lat: 41.0082, lon: 28.9784 },
        { name: "Cairo", country: "EG", lat: 30.0444, lon: 31.2357 },
        { name: "Rio de Janeiro", country: "BR", lat: -22.9068, lon: -43.1729 },
        { name: "Buenos Aires", country: "AR", lat: -34.6037, lon: -58.3816 },
        { name: "Mexico City", country: "MX", lat: 19.4326, lon: -99.1332 },
        { name: "Vancouver", country: "CA", lat: 49.2827, lon: -123.1207 },
        { name: "Los Angeles", country: "US", lat: 34.0522, lon: -118.2437 },
        { name: "San Francisco", country: "US", lat: 37.7749, lon: -122.4194 },
        { name: "Chicago", country: "US", lat: 41.8781, lon: -87.6298 },
        { name: "Miami", country: "US", lat: 25.7617, lon: -80.1918 },
        { name: "Barcelona", country: "ES", lat: 41.3851, lon: 2.1734 },
        { name: "Vienna", country: "AT", lat: 48.2082, lon: 16.3738 },
        { name: "Zurich", country: "CH", lat: 47.3769, lon: 8.5417 },
        { name: "Brussels", country: "BE", lat: 50.8503, lon: 4.3517 },
        { name: "Stockholm", country: "SE", lat: 59.3293, lon: 18.0686 },
        { name: "Oslo", country: "NO", lat: 59.9139, lon: 10.7522 },
        { name: "Helsinki", country: "FI", lat: 60.1699, lon: 24.9384 },
        { name: "Hong Kong", country: "HK", lat: 22.3193, lon: 114.1694 },
        { name: "Shanghai", country: "CN", lat: 31.2304, lon: 121.4737 },
        { name: "Cape Town", country: "ZA", lat: -33.9249, lon: 18.4241 },
        { name: "Johannesburg", country: "ZA", lat: -26.2041, lon: 28.0473 },
        { name: "Nairobi", country: "KE", lat: -1.2921, lon: 36.8219 },
        { name: "Lagos", country: "NG", lat: 6.5244, lon: 3.3792 },
        { name: "Athens", country: "GR", lat: 37.9838, lon: 23.7275 },
        { name: "Prague", country: "CZ", lat: 50.0755, lon: 14.4378 },
        { name: "Warsaw", country: "PL", lat: 52.2297, lon: 21.0122 },
        { name: "Lisbon", country: "PT", lat: 38.7223, lon: -9.1393 },
        { name: "Dublin", country: "IE", lat: 53.3498, lon: -6.2603 },
        { name: "Copenhagen", country: "DK", lat: 55.6761, lon: 12.5683 },
    ],

    initAutocomplete(searchInput, searchResults, onSelectCallback) {
        if (!searchInput || !searchResults) return;

        let searchTimeout = null;
        let selectedIndex = -1;

        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            const query = searchInput.value.trim().toLowerCase();
            selectedIndex = -1;

            if (query.length < 2) {
                searchResults.classList.add('d-none');
                return;
            }

            // Local Search
            const localMatches = this.CITY_DATASET.filter(city =>
                city.name.toLowerCase().includes(query)
            ).slice(0, 5);

            if (localMatches.length > 0) {
                this.renderResults(localMatches.map(m => ({
                    lat: m.lat,
                    lon: m.lon,
                    display_name: `${m.name}, ${m.country}`
                })), searchResults, searchInput, (data) => {
                    selectedIndex = -1;
                    onSelectCallback(data);
                });
            }

            // API Search
            searchTimeout = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/geocode/search?q=${encodeURIComponent(query)}`);
                    const apiData = await res.json();

                    const combined = [...localMatches
                        .filter(m => m.lat !== undefined && m.lon !== undefined)
                        .map(m => ({
                            lat: m.lat.toString(),
                            lon: m.lon.toString(),
                            display_name: `${m.name}, ${m.country}`
                        }))];

                    apiData.forEach(item => {
                        const isDuplicate = combined.some(c =>
                            Math.abs(parseFloat(c.lat) - parseFloat(item.lat)) < 0.01 &&
                            Math.abs(parseFloat(c.lon) - parseFloat(item.lon)) < 0.01
                        );
                        if (!isDuplicate && combined.length < 8) {
                            combined.push(item);
                        }
                    });

                    this.renderResults(combined, searchResults, searchInput, (data) => {
                        selectedIndex = -1;
                        onSelectCallback(data);
                    });
                } catch (err) {
                    console.error("Search failed:", err);
                }
            }, 300);
        });

        // Keyboard Navigation
        searchInput.addEventListener('keydown', (e) => {
            const items = searchResults.querySelectorAll('.search-result-item');
            if (items.length === 0) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % items.length;
                this.updateSelectedStatus(items, selectedIndex);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                this.updateSelectedStatus(items, selectedIndex);
            } else if (e.key === 'Enter') {
                if (selectedIndex >= 0) {
                    e.preventDefault();
                    items[selectedIndex].click();
                }
            } else if (e.key === 'Escape') {
                searchResults.classList.add('d-none');
                searchInput.blur();
            }
        });

        // Click Outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.add('d-none');
            }
        });
    },

    updateSelectedStatus(items, selectedIndex) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('active');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('active');
            }
        });
    },

    renderResults(data, searchResults, searchInput, onSelect) {
        if (!searchResults) return;

        if (!data || data.length === 0) {
            searchResults.innerHTML = '<div class="p-3 text-muted small">No results found</div>';
        } else {
            searchResults.innerHTML = data.slice(0, 8).map(item => `
                <div class="search-result-item" data-lat="${item.lat}" data-lon="${item.lon}" data-name="${item.display_name.split(',')[0]}">
                    <i class="fas fa-location-dot"></i>
                    <div class="d-flex flex-column">
                        <span class="fw-bold">${item.display_name.split(',')[0]}</span>
                        <small class="text-muted" style="font-size: 0.75rem;">${item.display_name}</small>
                    </div>
                </div>
            `).join('');

            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.onclick = () => {
                    const lat = item.getAttribute('data-lat');
                    const lon = item.getAttribute('data-lon');
                    const name = item.getAttribute('data-name');
                    searchInput.value = name;
                    searchResults.classList.add('d-none');
                    onSelect({ lat, lon, name });
                };
            });
        }
        searchResults.classList.remove('d-none');
    },
    async loadPakistanCities() {
        try {
            const res = await fetch('/assets/pakistan_cities.json');
            if (res.ok) {
                const cities = await res.json();
                cities.forEach(city => {
                     // Check if already in dataset to avoid duplicates
                     const exists = this.CITY_DATASET.some(c => c.name === city.name && c.country === city.country);
                     if (!exists) {
                         this.CITY_DATASET.push(city);
                     }
                });
                console.log("Loaded Pakistan cities:", cities.length);
            }
        } catch (e) {
            console.error("Failed to load Pakistan cities:", e);
        }
    }
};
window.AutocompleteUtils = AutocompleteUtils;
// Load external data immediately
AutocompleteUtils.loadPakistanCities();