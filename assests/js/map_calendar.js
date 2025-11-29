document.addEventListener('DOMContentLoaded', function() {
    // --- Map Initialization ---
    const map = L.map('map').setView([51.505, -0.09], 5); // Default to London, Zoomed out

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Add a marker to the map
    let marker = L.marker([51.505, -0.09]).addTo(map);

    // Try to get user's location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            map.setView([lat, lon], 8);
            marker.setLatLng([lat, lon]); // Update marker position
            updateWeather(lat, lon);
        }, () => {
            // Fallback if permission denied or error
            updateWeather(51.505, -0.09);
        });
    } else {
        updateWeather(51.505, -0.09);
    }

    // Update weather on map move
    map.on('moveend', function() {
        const center = map.getCenter();
        marker.setLatLng(center); // Move marker to center
        updateWeather(center.lat, center.lng);
    });

    // --- Map Controls ---

    // Search Functionality
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('location-search');

    async function searchLocation() {
        const query = searchInput.value;
        if (!query) return;

        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`;

        try {
            const res = await fetch(url);
            const data = await res.json();

            if (data && data.length > 0) {
                const lat = parseFloat(data[0].lat);
                const lon = parseFloat(data[0].lon);
                map.setView([lat, lon], 10); // Zoom in on result
                marker.setLatLng([lat, lon]);
                updateWeather(lat, lon);
            } else {
                alert('Location not found');
            }
        } catch (error) {
            console.error("Search error:", error);
            alert('Error searching for location');
        }
    }

    searchBtn.addEventListener('click', searchLocation);
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchLocation();
        }
    });

    // Locate Me Functionality
    document.getElementById('locate-btn').addEventListener('click', function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                map.setView([lat, lon], 8);
                marker.setLatLng([lat, lon]);
                updateWeather(lat, lon);
            }, () => {
                alert('Unable to retrieve your location');
            });
        } else {
            alert('Geolocation is not supported by your browser');
        }
    });


    async function updateWeather(lat, lon) {
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m`;
        const geocodeUrl = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`;

        // Show loading state
        document.getElementById('weather-city').textContent = "Loading...";

        try {
            // Fetch Weather
            const weatherRes = await fetch(weatherUrl);
            const weatherData = await weatherRes.json();

            // Fetch City Name (Reverse Geocoding)
            // Note: Nominatim requires a User-Agent, browsers send one automatically.
            const geoRes = await fetch(geocodeUrl);
            const geoData = await geoRes.json();

            // Update UI
            if (weatherData.current) {
                document.getElementById('weather-temp').textContent = Math.round(weatherData.current.temperature_2m);
                document.getElementById('weather-wind').textContent = `${weatherData.current.wind_speed_10m} km/h`;
                document.getElementById('weather-humidity').textContent = `${weatherData.current.relative_humidity_2m}%`;
            }

            let locationName = "Unknown Location";
            if (geoData.address) {
                locationName = geoData.address.city || geoData.address.town || geoData.address.village || geoData.address.county || "Unknown Location";
            }
            document.getElementById('weather-city').textContent = locationName;

        } catch (error) {
            console.error("Error fetching data:", error);
            document.getElementById('weather-city').textContent = "Error loading data";
        }
    }

    // --- Calendar Initialization ---
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        let currentEvent = null; // To store the event being deleted

        // Load events from LocalStorage
        let savedEvents = JSON.parse(localStorage.getItem('synocast_events')) || [];

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay'
            },
            themeSystem: 'bootstrap5',
            events: savedEvents,
            editable: true,
            selectable: true,
            select: function(info) {
                // Open Add Event Modal
                document.getElementById('addEventForm').reset();
                document.getElementById('eventDate').value = info.startStr;
                const modal = new bootstrap.Modal(document.getElementById('addEventModal'));
                modal.show();
            },
            eventClick: function(info) {
                // Open Delete Event Modal
                currentEvent = info.event;
                document.getElementById('deleteEventTitle').textContent = currentEvent.title;
                document.getElementById('deleteEventDate').textContent = currentEvent.start.toLocaleDateString();
                const modal = new bootstrap.Modal(document.getElementById('deleteEventModal'));
                modal.show();
            },
            eventDrop: function(info) {
                updateEventInStorage(info.event);
            }
        });

        calendar.render();

        // --- Event Management ---

        // Save Event
        const saveBtn = document.getElementById('saveEventBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                const title = document.getElementById('eventTitle').value;
                const date = document.getElementById('eventDate').value;
                const description = document.getElementById('eventDescription').value;
                const color = document.getElementById('eventColor').value;

                if (title) {
                    const newEvent = {
                        id: Date.now().toString(), // Simple unique ID
                        title: title,
                        start: date,
                        description: description,
                        backgroundColor: color,
                        borderColor: color
                    };

                    calendar.addEvent(newEvent);
                    saveEventToStorage(newEvent);

                    // Close Modal
                    const modalEl = document.getElementById('addEventModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    modal.hide();
                } else {
                    alert('Please enter an event title.');
                }
            });
        }

        // Delete Event
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                if (currentEvent) {
                    currentEvent.remove();
                    removeEventFromStorage(currentEvent.id);
                    currentEvent = null;

                    // Close Modal
                    const modalEl = document.getElementById('deleteEventModal');
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    modal.hide();
                }
            });
        }

        // --- LocalStorage Helpers ---

        function saveEventToStorage(event) {
            savedEvents.push(event);
            localStorage.setItem('synocast_events', JSON.stringify(savedEvents));
        }

        function removeEventFromStorage(eventId) {
            savedEvents = savedEvents.filter(e => e.id !== eventId);
            localStorage.setItem('synocast_events', JSON.stringify(savedEvents));
        }

        function updateEventInStorage(updatedEvent) {
            const index = savedEvents.findIndex(e => e.id === updatedEvent.id);
            if (index !== -1) {
                savedEvents[index].start = updatedEvent.startStr;
                savedEvents[index].end = updatedEvent.endStr;
                localStorage.setItem('synocast_events', JSON.stringify(savedEvents));
            }
        }
    }
});
