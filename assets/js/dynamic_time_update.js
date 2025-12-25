
/**
 * Real-time clock update for the top navigation bar.
 * Updates the display string based on the city's UTC offset.
 */
document.addEventListener('DOMContentLoaded', function() {
    const timeDisplay = document.getElementById('dynamic_time_display');
    if (!timeDisplay) return;

    function updateTime() {
        const city = timeDisplay.getAttribute('data-city') || "Unknown";
        const region = timeDisplay.getAttribute('data-region') || "";
        const utcOffset = timeDisplay.getAttribute('data-offset') || "+0000";
        const gmtLabel = timeDisplay.getAttribute('data-gmt') || "GMT+00:00";

        try {
            // Convert offset string ("+0500" or "-0300") to hours/minutes
            const sign = utcOffset.startsWith('-') ? -1 : 1;
            const hours = parseInt(utcOffset.substring(1, 3)) * sign;
            const minutes = parseInt(utcOffset.substring(3)) * sign;
            
            // Get current UTC time
            const now = new Date();
            const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
            
            // Apply city offset
            const cityTime = new Date(utcTime + (hours * 3600000) + (minutes * 60000));
            
            // Format: Saturday, September 27, 2024, 14:00
            const options = { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric', 
                year: 'numeric',
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false
            };
            
            const formattedDate = cityTime.toLocaleTimeString('en-US', options).replace(/ at /i, ', ');
            
            const locationPart = region ? `${city} - ${region}` : city;
            timeDisplay.textContent = `${formattedDate} Time zone in ${locationPart} (${gmtLabel})`;
        } catch (e) {
            // Silently fail or use static template value
        }
    }

    // Listen for global location grant
    window.addEventListener('synocast_location_granted', async (e) => {
        handleLocationChange(e.detail.lat, e.detail.lon);
    });

    // Immediate check if location is already granted
    if (window.synocast_current_loc) {
        handleLocationChange(window.synocast_current_loc.lat, window.synocast_current_loc.lon);
    }

    async function handleLocationChange(lat, lon) {
        try {
            // Reverse geocode to get city/region
            const geoUrl = `/api/geocode/reverse?lat=${lat}&lon=${lon}`;
            const res = await fetch(geoUrl);
            const data = await res.json();
            
            if (data.address) {
                const city = data.address.city || data.address.town || data.address.village || data.address.suburb || "My Location";
                const region = data.address.state || data.address.province || "";
                
                // Fetch weather to get timezone offset
                const weatherUrl = `/api/weather?lat=${lat}&lon=${lon}`;
                const weatherRes = await fetch(weatherUrl);
                const weatherData = await weatherRes.json();
                
                if (weatherData.current) {
                    const offsetSeconds = weatherData.current.timezone;
                    const offsetHours = Math.floor(offsetSeconds / 3600);
                    const offsetMinutes = Math.abs(Math.floor((offsetSeconds % 3600) / 60));
                    
                    const sign = offsetHours >= 0 ? '+' : '-';
                    const absHours = Math.abs(offsetHours);
                    const formattedOffset = `${sign}${absHours.toString().padStart(2, '0')}${offsetMinutes.toString().padStart(2, '0')}`;
                    const gmtLabel = `GMT${sign}${absHours.toString().padStart(2, '0')}:${offsetMinutes.toString().padStart(2, '0')}`;
                    
                    // Update attributes
                    timeDisplay.setAttribute('data-city', city);
                    timeDisplay.setAttribute('data-region', region);
                    timeDisplay.setAttribute('data-offset', formattedOffset);
                    timeDisplay.setAttribute('data-gmt', gmtLabel);
                    
                    // Trigger immediate update
                    updateTime();
                    
                    // Update server session
                    const csrfToken = document.querySelector('meta[name="_csrf_token"]')?.getAttribute('content');
                    fetch('/api/update-session-location', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({ city, region, utc_offset: formattedOffset })
                    });
                }
            }
        } catch (err) {
            console.warn("Failed to update top bar location:", err);
        }
    }

    // Update every minute (on the minute mark)
    updateTime();
    setTimeout(() => {
        updateTime();
        setInterval(updateTime, 60000);
    }, (60 - new Date().getSeconds()) * 1000);
});
