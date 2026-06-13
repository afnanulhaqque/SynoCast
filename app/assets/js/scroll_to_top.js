function scrollToTop(e) {
    if (e) {
        e.preventDefault();
    }
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) {
        console.warn("Scroll listener: Navbar element not found");
        return;
    }
    
    console.log("Scroll listener: Navbar element found, initializing");
    
    function handleScroll() {
        if (window.scrollY > 50) {
            if (!navbar.classList.contains('scrolled')) {
                navbar.classList.add('scrolled');
                console.log("Navbar scroll: Added 'scrolled' class");
            }
        } else {
            if (navbar.classList.contains('scrolled')) {
                navbar.classList.remove('scrolled');
                console.log("Navbar scroll: Removed 'scrolled' class");
            }
        }
    }
    
    // Check initial state
    handleScroll();
    
    window.addEventListener('scroll', handleScroll);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavbarScroll);
} else {
    initNavbarScroll();
}
