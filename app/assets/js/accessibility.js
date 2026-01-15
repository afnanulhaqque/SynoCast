/**
 * SynoCast Accessibility & Keyboard Navigation Handler
 */

class AccessibilityHandler {
    constructor() {
        this.contrastMode = localStorage.getItem('synocast_contrast_mode') || 'default';
        this.fontSize = localStorage.getItem('synocast_font_size') || 'medium';
        this.reducedMotion = localStorage.getItem('synocast_reduced_motion') === 'true';
        
        this.init();
    }

    init() {
        this.applyContrastMode();
        this.applyFontSize();
        this.applyReducedMotion();
        this.setupToolbar();
        this.setupKeyboardNavigation();
        this.setupScreenReaderAnnouncer();
    }

    applyContrastMode() {
        document.documentElement.setAttribute('data-contrast', this.contrastMode);
    }

    applyFontSize() {
        document.documentElement.setAttribute('data-font-size', this.fontSize);
    }

    applyReducedMotion() {
        if (this.reducedMotion) {
            document.documentElement.classList.add('reduce-motion');
        } else {
            document.documentElement.classList.remove('reduce-motion');
        }
    }

    setupToolbar() {
        const toolbar = document.createElement('div');
        toolbar.id = 'accessibility-toolbar';
        toolbar.className = 'accessibility-toolbar';
        toolbar.setAttribute('role', 'dialog');
        toolbar.setAttribute('aria-labelledby', 'acc-toolbar-title');
        
        toolbar.innerHTML = `
            <h5 id="acc-toolbar-title" class="fw-bold mb-3">Accessibility Settings</h5>
            
            <div class="accessibility-option">
                <label for="high-contrast-toggle">High Contrast Mode</label>
                <div class="toggle-switch" id="high-contrast-toggle-trigger">
                    <input type="checkbox" id="high-contrast-toggle" ${this.contrastMode === 'high' ? 'checked' : ''}>
                    <span class="slider"></span>
                </div>
            </div>

            <div class="accessibility-option">
                <label for="reduced-motion-toggle">Reduced Motion</label>
                <div class="toggle-switch" id="reduced-motion-trigger">
                    <input type="checkbox" id="reduced-motion-toggle" ${this.reducedMotion ? 'checked' : ''}>
                    <span class="slider"></span>
                </div>
            </div>

            <div class="mt-3">
                <label class="d-block mb-2 small fw-bold">Font Size</label>
                <div class="font-size-controls">
                    <button class="font-size-btn" data-size="small" aria-label="Small Font">A</button>
                    <button class="font-size-btn" data-size="medium" aria-label="Medium Font">A</button>
                    <button class="font-size-btn" data-size="large" aria-label="Large Font">A</button>
                    <button class="font-size-btn" data-size="xlarge" aria-label="Extra Large Font">A</button>
                </div>
            </div>

            <div class="mt-4 border-top pt-3">
                <button id="close-acc-toolbar" class="btn btn-sm btn-outline-theme w-100 rounded-pill">Close</button>
            </div>
        `;

        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'accessibility-toggle';
        toggleBtn.className = 'accessibility-toolbar-toggle';
        toggleBtn.setAttribute('aria-label', 'Open accessibility settings');
        toggleBtn.setAttribute('aria-haspopup', 'dialog');
        toggleBtn.innerHTML = '<i class="fas fa-universal-access fa-lg"></i>';

        document.body.appendChild(toggleBtn);
        document.body.appendChild(toolbar);

        // Event Listeners
        toggleBtn.addEventListener('click', () => {
            toolbar.classList.toggle('show');
            const isVisible = toolbar.classList.contains('show');
            toggleBtn.setAttribute('aria-expanded', isVisible);
            if (isVisible) {
                toolbar.querySelector('input').focus();
            }
        });

        document.getElementById('close-acc-toolbar').addEventListener('click', () => {
            toolbar.classList.remove('show');
            toggleBtn.setAttribute('aria-expanded', 'false');
            toggleBtn.focus();
        });

        document.getElementById('high-contrast-toggle').addEventListener('change', (e) => {
            this.contrastMode = e.target.checked ? 'high' : 'default';
            localStorage.setItem('synocast_contrast_mode', this.contrastMode);
            this.applyContrastMode();
            this.announce(this.contrastMode === 'high' ? 'High contrast mode enabled' : 'High contrast mode disabled');
        });

        document.getElementById('reduced-motion-toggle').addEventListener('change', (e) => {
            this.reducedMotion = e.target.checked;
            localStorage.setItem('synocast_reduced_motion', this.reducedMotion);
            this.applyReducedMotion();
            this.announce(this.reducedMotion ? 'Animations reduced' : 'Animations enabled');
        });

        toolbar.querySelectorAll('.font-size-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.fontSize = btn.dataset.size;
                localStorage.setItem('synocast_font_size', this.fontSize);
                this.applyFontSize();
                this.announce(`Font size set to ${this.fontSize}`);
            });
        });

        // Close on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && toolbar.classList.contains('show')) {
                toolbar.classList.remove('show');
                toggleBtn.focus();
            }
        });
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Only trigger if not typing in an input/textarea
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
                if (e.key === 'Escape') {
                    document.activeElement.blur();
                }
                return;
            }

            switch(e.key.toLowerCase()) {
                case '/':
                    e.preventDefault();
                    document.getElementById('weather-search-input')?.focus();
                    break;
                case 't':
                    document.getElementById('tab-today')?.click();
                    break;
                case 'w':
                    document.getElementById('tab-week')?.click();
                    break;
                case 'a':
                    document.getElementById('tab-analytics')?.click();
                    break;
                case 'e':
                    document.getElementById('tab-extended')?.click();
                    break;
                case 'c':
                    document.getElementById('btn-celsius')?.click();
                    break;
                case 'f':
                    document.getElementById('btn-fahrenheit')?.click();
                    break;
                case '?':
                    this.showKeyboardShortcuts();
                    break;
            }
        });
    }

    setupScreenReaderAnnouncer() {
        const announcer = document.createElement('div');
        announcer.id = 'sr-announcer';
        announcer.className = 'sr-only';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        document.body.appendChild(announcer);
        this.announcer = announcer;
    }

    announce(message) {
        if (this.announcer) {
            this.announcer.textContent = message;
        }
    }

    showKeyboardShortcuts() {
        // Find or create a shortcuts modal
        let modal = document.getElementById('shortcuts-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'shortcuts-modal';
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            modal.setAttribute('aria-hidden', 'true');
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content rounded-4 border-0 shadow-lg">
                        <div class="modal-header border-0 pb-0">
                            <h5 class="modal-title fw-bold">Keyboard Shortcuts</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body p-4">
                            <div class="row g-3">
                                <div class="col-6"><span class="keyboard-hint">/</span> Search</div>
                                <div class="col-6"><span class="keyboard-hint">T</span> Today Forecast</div>
                                <div class="col-6"><span class="keyboard-hint">W</span> Weekly Forecast</div>
                                <div class="col-6"><span class="keyboard-hint">A</span> Analytics</div>
                                <div class="col-6"><span class="keyboard-hint">E</span> Extended Forecast</div>
                                <div class="col-6"><span class="keyboard-hint">C/F</span> Temperature Unit</div>
                                <div class="col-6"><span class="keyboard-hint">?</span> This Help</div>
                                <div class="col-6"><span class="keyboard-hint">Esc</span> Close/Blur</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

// Global Accessibility Broadcaster for other scripts to use
window.SynoCastAccessibility = {
    announce: (msg) => {
        const handler = window.synocastAccessibilityHandler;
        if (handler) handler.announce(msg);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.synocastAccessibilityHandler = new AccessibilityHandler();
});
