/**
 * Shared weather utilities for SynoCast
 */
const WeatherUtils = {
    /**
     * Maps OpenWeatherMap condition IDs to FontAwesome icon classes and animations
     * @param {number} id - OWM Condition ID
     * @param {string} icon - OWM Icon string (to check day/night)
     * @returns {Object} { icon: string, animation: string, color: string }
     */
    getIconClass: function(id, iconCode = '') {
        const isNight = iconCode.includes('n');
        let icon = 'fa-cloud';
        let animation = 'weather-icon-cloud';
        let color = 'weather-icon-cloud';

        if (id >= 200 && id < 300) {
            icon = 'fa-bolt';
            animation = 'weather-icon-thunderstorm';
            color = 'weather-icon-thunderstorm';
        } else if (id >= 300 && id < 500) {
            icon = 'fa-cloud-rain';
            animation = 'weather-icon-rain';
            color = 'weather-icon-rain';
        } else if (id >= 500 && id < 600) {
            icon = 'fa-cloud-showers-heavy';
            animation = 'weather-icon-showers';
            color = 'weather-icon-showers';
        } else if (id >= 600 && id < 700) {
            icon = 'fa-snowflake';
            animation = 'weather-icon-snow';
            color = 'weather-icon-snow';
        } else if (id >= 700 && id < 800) {
            icon = 'fa-smog';
            animation = 'weather-icon-fog';
            color = 'weather-icon-fog';
        } else if (id === 800) {
            if (isNight) {
                icon = 'fa-moon';
                animation = 'weather-icon-moon';
                color = 'weather-icon-moon';
            } else {
                icon = 'fa-sun';
                animation = 'weather-icon-sun';
                color = 'weather-icon-sun';
            }
        } else if (id > 800 && id < 803) {
            if (isNight) {
                icon = 'fa-cloud-moon';
                animation = 'weather-icon-moon';
                color = 'weather-icon-moon';
            } else {
                icon = 'fa-cloud-sun';
                animation = 'weather-icon-sun';
                color = 'weather-icon-sun';
            }
        }

        return { icon, animation, color };
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
