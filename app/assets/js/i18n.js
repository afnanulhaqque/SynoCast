/**
 * SynoCast Internationalization (i18n) Utility
 * Handles multi-language support, RTL rendering, and language persistence.
 */

class I18nManager {
    constructor() {
        this.translations = {};
        this.currentLang = localStorage.getItem('synocast_lang') || this.detectBrowserLang();
        this.isRTL = ['ar', 'ur', 'he', 'fa'].includes(this.currentLang);
    }

    async init() {
        try {
            const response = await fetch('/assets/translations.json');
            this.translations = await response.json();
            
            // If currentLang is not in translations, fallback to 'en'
            if (!this.translations[this.currentLang]) {
                this.currentLang = 'en';
            }
            
            this.applyTranslations();
            this.updateRTLLayout();
            
            // Dispatch event when ready
            window.dispatchEvent(new CustomEvent('i18nReady', { detail: { lang: this.currentLang } }));
        } catch (error) {
            console.error('Failed to load translations:', error);
        }
    }

    detectBrowserLang() {
        const lang = navigator.language || navigator.userLanguage;
        const shortLang = lang.split('-')[0];
        return shortLang;
    }

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            this.isRTL = ['ar', 'ur', 'he', 'fa'].includes(lang);
            localStorage.setItem('synocast_lang', lang);
            this.applyTranslations();
            this.updateRTLLayout();
            
            // Save to backend if user is logged in
            this.savePreferenceToBackend(lang);
            
            window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
        }
    }

    async savePreferenceToBackend(lang) {
        try {
            // Only try if we have a session (session handling is usually handled by server)
            // But we can hit an endpoint that updates it if logged in.
            const response = await fetch('/api/user/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: lang })
            });
            // Silent fail if not logged in (e.g. 401)
        } catch (e) {
            // Ignore
        }
    }

    updateRTLLayout() {
        document.documentElement.setAttribute('dir', this.isRTL ? 'rtl' : 'ltr');
        document.documentElement.setAttribute('lang', this.currentLang);
        
        if (this.isRTL) {
            document.body.classList.add('rtl-mode');
        } else {
            document.body.classList.remove('rtl-mode');
        }
    }

    t(key, fallback = null) {
        const keys = key.split('.');
        let result = this.translations[this.currentLang];
        
        for (const k of keys) {
            if (result && result[k]) {
                result = result[k];
            } else {
                // Fallback to English if current language fails
                let englishFallback = this.translations['en'];
                for (const ek of keys) {
                    if (englishFallback && englishFallback[ek]) {
                        englishFallback = englishFallback[ek];
                    } else {
                        englishFallback = null;
                        break;
                    }
                }
                return englishFallback || fallback || key;
            }
        }
        
        return result || fallback || key;
    }

    applyTranslations() {
        // Tag elements with data-t key to have them translated automatically
        const elements = document.querySelectorAll('[data-t]');
        elements.forEach(el => {
            const key = el.getAttribute('data-t');
            const translation = this.t(key);
            
            if (el.tagName === 'INPUT' && (el.type === 'placeholder' || el.getAttribute('placeholder'))) {
                el.setPlaceholder(translation);
            } else {
                el.textContent = translation;
            }
        });

        // Translate placeholders separately if needed
        const placeholders = document.querySelectorAll('[data-t-placeholder]');
        placeholders.forEach(el => {
            const key = el.getAttribute('data-t-placeholder');
            el.placeholder = this.t(key);
        });
    }
}

// Global instance
const i18n = new I18nManager();
document.addEventListener('DOMContentLoaded', () => i18n.init());

// Helper for inputs
Element.prototype.setPlaceholder = function(text) {
    this.placeholder = text;
};
