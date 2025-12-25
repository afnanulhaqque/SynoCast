/**
 * Shared weather utilities for SynoCast
 */
const WeatherUtils = {
    /**
     * Maps OpenWeatherMap condition IDs to FontAwesome icon classes
     * @param {number} id - OWM Condition ID
     * @param {string} icon - OWM Icon string (to check day/night)
     * @returns {string} FontAwesome class name
     */
    getIconClass: function(id, iconCode = '') {
        const isNight = iconCode.includes('n');
        
        if (id >= 200 && id < 300) return 'fa-bolt'; // Thunderstorm
        if (id >= 300 && id < 500) return 'fa-cloud-rain'; // Drizzle
        if (id >= 500 && id < 600) return 'fa-cloud-showers-heavy'; // Rain
        if (id >= 600 && id < 700) return 'fa-snowflake'; // Snow
        if (id >= 700 && id < 800) return 'fa-smog'; // Atmosphere (Fog/Smog)
        if (id === 800) return isNight ? 'fa-moon' : 'fa-sun'; // Clear
        if (id > 800 && id < 803) return isNight ? 'fa-cloud-moon' : 'fa-cloud-sun'; // Few clouds
        return 'fa-cloud'; // Overcast
    },

    /**
     * Converts Celsius to Fahrenheit
     * @param {number} celsius 
     * @returns {number}
     */
    celsiusToFahrenheit: function(celsius) {
        return Math.round((celsius * 9/5) + 32);
    },

    /**
     * Formats wind speed
     * @param {number} speed - in m/s
     * @returns {string}
     */
    formatWind: function(speed) {
        // Convert m/s to km/h (optional, OWM returns m/s)
        return `${Math.round(speed * 3.6)} km/h`;
    }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.WeatherUtils = WeatherUtils;
    window.SecurityUtils = {
        getCsrfToken: function() {
            return document.querySelector('meta[name="_csrf_token"]')?.getAttribute('content');
        }
    };

    window.ToastUtils = {
        show: function(title, message, type = 'info', duration = 5000) {
            const container = document.getElementById('synocast-toast-container');
            if (!container) return;

            const iconClass = type === 'error' ? 'fa-circle-xmark' : 
                             type === 'warning' ? 'fa-triangle-exclamation' : 
                             'fa-circle-info';

            const toast = document.createElement('div');
            toast.className = `synocast-toast ${type}`;
            toast.innerHTML = `
                <div class="synocast-toast-icon">
                    <i class="fa-solid ${iconClass} fs-5"></i>
                </div>
                <div class="synocast-toast-content">
                    <div class="synocast-toast-title">${title}</div>
                    <div class="synocast-toast-message">${message}</div>
                </div>
                <div class="synocast-toast-close">
                    <i class="fa-solid fa-xmark"></i>
                </div>
            `;

            container.appendChild(toast);
            
            // Add close listener
            toast.querySelector('.synocast-toast-close').onclick = () => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 500);
            };

            // Force reflow
            toast.offsetHeight;
            toast.classList.add('show');

            if (duration > 0) {
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.classList.remove('show');
                        setTimeout(() => toast.remove(), 500);
                    }
                }, duration);
            }
        }
    };
}
