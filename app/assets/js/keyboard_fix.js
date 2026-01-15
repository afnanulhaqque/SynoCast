/**
 * Mobile Keyboard Optimization
 * Ensures input fields remain visible when the virtual keyboard appears on mobile devices.
 * Automatically scrolls the focused input into view and adjusts layout.
 */

document.addEventListener('DOMContentLoaded', function() {
    let initialViewportHeight = window.innerHeight;
    let isKeyboardOpen = false;

    // Detect if device is mobile
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (window.innerWidth <= 768);
    }

    // Handle keyboard open/close detection
    function handleViewportResize() {
        const currentHeight = window.innerHeight;
        const heightDifference = initialViewportHeight - currentHeight;
        
        // Keyboard is likely open if viewport shrinks by more than 150px
        if (heightDifference > 150 && isMobileDevice()) {
            if (!isKeyboardOpen) {
                isKeyboardOpen = true;
                document.body.classList.add('keyboard-open');
            }
        } else {
            if (isKeyboardOpen) {
                isKeyboardOpen = false;
                document.body.classList.remove('keyboard-open');
            }
        }
    }

    // Listen for viewport changes (keyboard open/close)
    window.addEventListener('resize', handleViewportResize);

    // Handle focus on all input fields
    document.body.addEventListener('focusin', function(e) {
        const target = e.target;
        
        if ((target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') && isMobileDevice()) {
            // Mark keyboard as opening
            document.body.classList.add('keyboard-opening');
            
            // Scroll the input into view with a delay to allow keyboard animation
            setTimeout(() => {
                // Get the input's position
                const rect = target.getBoundingClientRect();
                const viewportHeight = window.innerHeight;
                
                // If input is in the bottom half of the screen, scroll it up
                if (rect.top > viewportHeight / 2) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center',
                        inline: 'nearest'
                    });
                }
                
                // For specific elements like chatbot input, scroll to bottom of container
                if (target.id === 'chatbot_input') {
                    const chatMessages = document.getElementById('chatbot_messages');
                    if (chatMessages) {
                        setTimeout(() => {
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        }, 100);
                    }
                }
                
                document.body.classList.remove('keyboard-opening');
            }, 300);
        }
    });

    // Handle blur (when input loses focus)
    document.body.addEventListener('focusout', function(e) {
        if ((e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') && isMobileDevice()) {
            // Small delay to allow keyboard to close
            setTimeout(() => {
                handleViewportResize();
            }, 100);
        }
    });

    // Initial check
    if (isMobileDevice()) {
        handleViewportResize();
    }
});
