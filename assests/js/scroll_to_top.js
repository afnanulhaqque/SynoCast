function scrollToTop(e) {
    if (e) {
        e.preventDefault();
    }
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}
