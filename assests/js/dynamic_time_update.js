document.addEventListener('DOMContentLoaded', function() {
    startClock();
});

function startClock() {
    const el = document.getElementById('dynamic_time_display');
    if (!el) return;

    // 1. Get the Backend Data
    const city = el.dataset.city;
    const region = el.dataset.region;
    const offsetStr = el.dataset.offset; // e.g. "+0500"
    const gmtLabel = el.dataset.gmt;     // e.g. "GMT+05:00"

    // 2. Parse Offset into Minutes
    const sign = offsetStr.slice(0, 1) === '+' ? 1 : -1;
    const hours = parseInt(offsetStr.slice(1, 3));
    const minutes = parseInt(offsetStr.slice(3, 5));
    const totalOffsetMinutes = sign * ((hours * 60) + minutes);

    function update() {
        // 3. Calculate Time for the Specific Timezone
        const now = new Date();
        const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
        const targetTime = new Date(utcTime + (totalOffsetMinutes * 60000));

        // 4. Format EXACTLY like Python: "%A, %B %d, %Y, %H:%M"
        // Example: Wednesday, November 26, 2025, 15:30
        
        const weekday = targetTime.toLocaleDateString('en-US', { weekday: 'long' });
        const month = targetTime.toLocaleDateString('en-US', { month: 'long' });
        const day = targetTime.getDate(); // 26
        const year = targetTime.getFullYear(); // 2025
        
        // Manual 24hr formatting to ensure "15:30" (not 3:30 PM)
        let h = targetTime.getHours();
        let m = targetTime.getMinutes();
        if (h < 10) h = '0' + h;
        if (m < 10) m = '0' + m;
        
        const timePart = `${h}:${m}`;

        // Reconstruct the full string
        const finalString = `${weekday}, ${month} ${day}, ${year}, ${timePart} Time zone in ${city} - ${region} (${gmtLabel})`;

        // 5. Update HTML
        el.innerText = finalString;
    }

    // Run immediately and every second
    update();
    setInterval(update, 1000);
}