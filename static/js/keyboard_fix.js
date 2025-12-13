/**
 * Mobile Virtual Keyboard Fix
 * Detects when the virtual keyboard opens (via visualViewport resize) and adjusts
 * the page layout to keep input fields visible.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Only run if visualViewport API is supported
    if (!window.visualViewport) return;

    const viewport = window.visualViewport;
    const body = document.body;
    
    // Function to handle viewport changes
    const handleViewportChange = () => {
        // Check if an input or textarea is currently focused
        const activeElement = document.activeElement;
        const isInput = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA';
        
        if (!isInput) return;

        // Calculate the difference between layout height and visual height
        // This roughly corresponds to the keyboard height
        const heightDiff = window.innerHeight - viewport.height;
        
        // If keyboard is likely open (significant height difference)
        if (heightDiff > 150) {
            // Get the bounding rect of the active element relative to the visual viewport
            const rect = activeElement.getBoundingClientRect();
            
            // If the element is hidden behind the keyboard (below the visual viewport height)
            // or very close to the bottom
            const bottomThreshold = viewport.height - 20; // 20px padding
            
            if (rect.bottom > bottomThreshold) {
                // Calculate how much we need to scroll/shift
                const scrollAmount = rect.bottom - bottomThreshold + 10;
                
                // Option 1: Scroll into view (standard behavior)
                // activeElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                
                // Option 2: Add padding to body to allow scrolling up
                // This is often smoother than forcing scroll
                const currentPaddingBottom = parseInt(body.style.paddingBottom || '0');
                if (currentPaddingBottom < heightDiff) {
                     body.style.paddingBottom = `${heightDiff}px`;
                     window.scrollTo(window.scrollX, window.scrollY + scrollAmount);
                }
            }
        } else {
            // Keyboard likely closed, reset padding
            body.style.paddingBottom = '0px';
        }
    };

    // Listen for resize and scroll events on the visualViewport
    viewport.addEventListener('resize', handleViewportChange);
    viewport.addEventListener('scroll', handleViewportChange);
    
    // Also listen for focus events to trigger check immediately
    document.addEventListener('focusin', handleViewportChange);
});
