
/**
 * Real-time clock update for the top navigation bar.
 * Updates the display string based on the city's UTC offset.
 */
document.addEventListener('DOMContentLoaded', function() {
    const timeDisplay = document.getElementById('dynamic_time_display');
    if (!timeDisplay) return;

    function updateTime() {
        const city = timeDisplay.getAttribute('data-city');
        const region = timeDisplay.getAttribute('data-region');
        const utcOffset = timeDisplay.getAttribute('data-offset');
        const gmtLabel = timeDisplay.getAttribute('data-gmt');

        if (!utcOffset) return;

        try {
            // Convert offset string ("+0500" or "-0300") to hours/minutes
            const hours = parseInt(utcOffset.substring(0, 3));
            const minutes = parseInt(utcOffset.substring(3));
            
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
            
            timeDisplay.textContent = `${formattedDate} Time zone in ${city} - ${region} (${gmtLabel})`;
        } catch (e) {
            console.error("Error updating dynamic time:", e);
        }
    }

    // Update every minute (on the minute mark)
    updateTime();
    setTimeout(() => {
        updateTime();
        setInterval(updateTime, 60000);
    }, (60 - new Date().getSeconds()) * 1000);
});
