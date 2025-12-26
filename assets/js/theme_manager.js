/**
 * SynoCast Theme Manager
 * Automatically changes UI themes based on weather conditions.
 */

const WEATHER_THEMES = {
    'Clear': {
        gradient: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        accent: '#6937f5',
        text: '#2d3436',
        cardBg: 'rgba(255, 255, 255, 0.8)',
        shadow: 'rgba(105, 55, 245, 0.1)'
    },
    'Clouds': {
        gradient: 'linear-gradient(135deg, #e6e9f0 0%, #eef1f5 100%)',
        accent: '#5a6268',
        text: '#2d3436',
        cardBg: 'rgba(255, 255, 255, 0.85)',
        shadow: 'rgba(0, 0, 0, 0.05)'
    },
    'Rain': {
        gradient: 'linear-gradient(135deg, #cfd9df 0%, #e2ebf0 100%)',
        accent: '#3498db',
        text: '#2d3436',
        cardBg: 'rgba(255, 255, 255, 0.8)',
        shadow: 'rgba(52, 152, 219, 0.1)'
    },
    'Snow': {
        gradient: 'linear-gradient(to top, #fff1eb 0%, #ace0f9 100%)',
        accent: '#54a0ff',
        text: '#2d3436',
        cardBg: 'rgba(255, 255, 255, 0.9)',
        shadow: 'rgba(0, 0, 0, 0.05)'
    },
    'Thunderstorm': {
        gradient: 'linear-gradient(135deg, #f5f7fa 0%, #bdc3c7 100%)',
        accent: '#f1c40f',
        text: '#2d3436',
        cardBg: 'rgba(255, 255, 255, 0.8)',
        shadow: 'rgba(241, 196, 15, 0.1)'
    }
};

function applyWeatherTheme(condition) {
    const theme = WEATHER_THEMES[condition] || WEATHER_THEMES['Clear'];
    const root = document.documentElement;

    root.style.setProperty('--weather-gradient', theme.gradient);
    root.style.setProperty('--weather-accent', theme.accent);
    root.style.setProperty('--weather-text', theme.text);
    root.style.setProperty('--weather-shadow', theme.shadow);
    root.style.setProperty('--weather-card-bg', theme.cardBg);

    // Apply background to body (subtle)
    document.body.style.background = theme.gradient;
    document.body.style.color = theme.text;
    
    // Update AI Suite Buttons (Tabs) - Default transparency, hover fill handled via CSS
    const aiTabs = document.querySelectorAll('#ai-tabs .nav-link');
    aiTabs.forEach(tab => {
        tab.style.transition = 'all 0.3s ease';
        tab.style.backgroundColor = 'transparent';
        tab.style.color = theme.text;
        tab.style.boxShadow = 'none';
        
        if (tab.classList.contains('active')) {
            tab.style.color = theme.accent;
            tab.style.fontWeight = '600';
        } else {
            tab.style.fontWeight = '400';
        }
    });

    console.log(`Applied theme for: ${condition}`);
}

window.applyWeatherTheme = applyWeatherTheme;
