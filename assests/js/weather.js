
document.addEventListener('DOMContentLoaded', function() {
    const btnCelsius = document.getElementById('btn-celsius');
    const btnFahrenheit = document.getElementById('btn-fahrenheit');
    const tempDisplays = document.querySelectorAll('.temp-display');

    // Helper to convert Celsius to Fahrenheit
    function celsiusToFahrenheit(celsius) {
        return Math.round((celsius * 9/5) + 32);
    }

    // Function to update the UI based on the selected unit
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

        // Update button styles
        if (unit === 'F') {
            btnFahrenheit.classList.remove('bg-light', 'text-dark');
            btnFahrenheit.classList.add('text-white');
            btnFahrenheit.style.backgroundColor = '#6937F5';

            btnCelsius.classList.remove('text-white');
            btnCelsius.classList.add('bg-light', 'text-dark');
            btnCelsius.style.backgroundColor = ''; // Remove inline style if any or reset
        } else {
            btnCelsius.classList.remove('bg-light', 'text-dark');
            btnCelsius.classList.add('text-white');
            btnCelsius.style.backgroundColor = '#6937F5';

            btnFahrenheit.classList.remove('text-white');
            btnFahrenheit.classList.add('bg-light', 'text-dark');
            btnFahrenheit.style.backgroundColor = '';
        }
    }

    // Event Listeners
    btnCelsius.addEventListener('click', function() {
        updateUnits('C');
    });

    btnFahrenheit.addEventListener('click', function() {
        updateUnits('F');
    });
});
