/**
 * Theme Mode Management
 * Enforces Light Mode based on updated design system.
 */

const Theme = {
    colors: {
        primary: '#2F2F2F',      // Soft Charcoal
        background: '#FAFAF8',   // Warm White
        accentWeather: '#6FAED9',// Muted Blue
        accentNews: '#6FAED9',   // Logo Blue
        textPrimary: '#1A1A1A',  // Almost Black
        textSecondary: '#6B6B6B' // Stone Gray
    },
    mode: 'light'
};

// Apply theme settings
function applyTheme() {
    // Force light mode on document root
    document.documentElement.setAttribute('data-theme', 'light');
    document.documentElement.style.setProperty('color-scheme', 'light');
    
    // Remote potential legacy dark mode markers
    document.body.classList.remove('dark-mode');
    
    // Store preference removed
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyTheme);
} else {
    applyTheme();
}

// Also run immediately to prevent flash if script is loaded in head
applyTheme();
