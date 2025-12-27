/**
 * SynoCast Timezone Management Utility
 * Handles automatic timezone detection, conversion, and display.
 */

class TimezoneManager {
    constructor() {
        this.userTimezone = localStorage.getItem('synocast_timezone') || Intl.DateTimeFormat().resolvedOptions().timeZone;
        this.utcOffset = 0;
    }

    init() {
        this.detectTimezone();
        this.updateTimeDisplays();
        
        // Listen for language changes if time formatting needs adjustment
        window.addEventListener('languageChanged', () => this.updateTimeDisplays());
    }

    detectTimezone() {
        // Fallback if Intl is not available
        if (!this.userTimezone) {
            this.userTimezone = 'UTC';
        }
        console.log('Detected timezone:', this.userTimezone);
    }

    setTimezone(tz) {
        this.userTimezone = tz;
        localStorage.setItem('synocast_timezone', tz);
        this.updateTimeDisplays();
        this.savePreferenceToBackend(tz);
        
        window.dispatchEvent(new CustomEvent('timezoneChanged', { detail: { timezone: tz } }));
    }

    async savePreferenceToBackend(tz) {
        try {
            await fetch('/api/user/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ timezone: tz })
            });
        } catch (e) {
            // Ignore
        }
    }

    formatTime(timestamp, options = {}) {
        const defaultOptions = {
            timeZone: this.userTimezone,
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        };
        
        const date = new Date(timestamp * 1000);
        return new Intl.DateTimeFormat(document.documentElement.lang || 'en', { ...defaultOptions, ...options }).format(date);
    }

    formatDate(timestamp, options = {}) {
        const defaultOptions = {
            timeZone: this.userTimezone,
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        };
        
        const date = new Date(timestamp * 1000);
        return new Intl.DateTimeFormat(document.documentElement.lang || 'en', { ...defaultOptions, ...options }).format(date);
    }

    updateTimeDisplays() {
        const timeElements = document.querySelectorAll('[data-timestamp]');
        timeElements.forEach(el => {
            const timestamp = parseInt(el.getAttribute('data-timestamp'));
            const type = el.getAttribute('data-time-type') || 'time';
            
            if (isNaN(timestamp)) return;
            
            if (type === 'time') {
                el.textContent = this.formatTime(timestamp);
            } else if (type === 'date') {
                el.textContent = this.formatDate(timestamp);
            } else if (type === 'full') {
                el.textContent = this.formatDate(timestamp, { hour: '2-digit', minute: '2-digit' });
            }
        });
    }
}

// Global instance
const tzManager = new TimezoneManager();
document.addEventListener('DOMContentLoaded', () => tzManager.init());
