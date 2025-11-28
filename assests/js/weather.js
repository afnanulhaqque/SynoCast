
document.addEventListener('DOMContentLoaded', function() {
    // --- Temperature Unit Toggle Logic ---
    const btnCelsius = document.getElementById('btn-celsius');
    const btnFahrenheit = document.getElementById('btn-fahrenheit');
    const tempDisplays = document.querySelectorAll('.temp-display');

    function celsiusToFahrenheit(celsius) {
        return Math.round((celsius * 9/5) + 32);
    }

    function updateUnits(unit) {
        tempDisplays.forEach(display => {
            const celsiusValue = parseFloat(display.getAttribute('data-celsius'));
            
            if (unit === 'F') {
                const fahrenheitValue = celsiusToFahrenheit(celsiusValue);
                display.textContent = `${fahrenheitValue}°`;
            } else {
                display.textContent = `${celsiusValue}°`;
            }
        });

        if (unit === 'F') {
            btnFahrenheit.classList.remove('bg-light', 'text-dark');
            btnFahrenheit.classList.add('text-white');
            btnFahrenheit.style.backgroundColor = '#6937F5';

            btnCelsius.classList.remove('text-white');
            btnCelsius.classList.add('bg-light', 'text-dark');
            btnCelsius.style.backgroundColor = ''; 
        } else {
            btnCelsius.classList.remove('bg-light', 'text-dark');
            btnCelsius.classList.add('text-white');
            btnCelsius.style.backgroundColor = '#6937F5';

            btnFahrenheit.classList.remove('text-white');
            btnFahrenheit.classList.add('bg-light', 'text-dark');
            btnFahrenheit.style.backgroundColor = '';
        }
    }

    if (btnCelsius && btnFahrenheit) {
        btnCelsius.addEventListener('click', function() {
            updateUnits('C');
        });

        btnFahrenheit.addEventListener('click', function() {
            updateUnits('F');
        });
    }

    // --- Forecast Tab Switching Logic ---
    const tabToday = document.getElementById('tab-today');
    const tabWeek = document.getElementById('tab-week');
    const forecastToday = document.getElementById('forecast-today');
    const forecastWeek = document.getElementById('forecast-week');

    function switchTab(tab) {
        if (tab === 'today') {
            // Show Today
            forecastToday.classList.remove('d-none');
            forecastWeek.classList.add('d-none');

            // Update Tab Styles
            tabToday.classList.remove('text-muted');
            tabToday.classList.add('text-dark');
            tabToday.style.opacity = '1';

            tabWeek.classList.remove('text-dark');
            tabWeek.classList.add('text-muted');
            tabWeek.style.opacity = '0.5';
        } else {
            // Show Week
            forecastWeek.classList.remove('d-none');
            forecastToday.classList.add('d-none');

            // Update Tab Styles
            tabWeek.classList.remove('text-muted');
            tabWeek.classList.add('text-dark');
            tabWeek.style.opacity = '1';

            tabToday.classList.remove('text-dark');
            tabToday.classList.add('text-muted');
            tabToday.style.opacity = '0.5';
        }
    }

    if (tabToday && tabWeek) {
        tabToday.addEventListener('click', function() {
            switchTab('today');
        });

        tabWeek.addEventListener('click', function() {
            switchTab('week');
        });
    }
});
