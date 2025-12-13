/**
 * Keyboard Overlay Optimization for Short Devices
 * Ensures input fields remain visible when the virtual keyboard appears on small screens.
 */

document.addEventListener('DOMContentLoaded', function() {
    const inputs = document.querySelectorAll('input, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            // Only apply fix for devices with height <= 667px (iPhone SE/8/etc)
            if (window.innerHeight <= 667) {
                // Small delay to allow keyboard to start opening
                setTimeout(() => {
                    this.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'nearest'
                    });
                }, 300);
            }
        });
    });

    // Also handle dynamic inputs (like inside modals)
    document.body.addEventListener('focusin', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            if (window.innerHeight <= 667) {
                setTimeout(() => {
                    e.target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'nearest'
                    });
                }, 300);
            }
        }
    });
});
