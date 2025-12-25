async function initI18n() {
    const lang = localStorage.getItem('synocast_lang') || 'en';
    const response = await fetch('/assets/translations.json');
    const translations = await response.json();
    
    applyTranslations(translations[lang]);
    
    // Set direction for Urdu
    document.documentElement.dir = (lang === 'ur') ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
}

function applyTranslations(strings) {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (strings[key]) {
            el.textContent = strings[key];
        }
    });
    
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (strings[key]) {
            el.placeholder = strings[key];
        }
    });
}

function switchLanguage(lang) {
    localStorage.setItem('synocast_lang', lang);
    location.reload();
}

document.addEventListener('DOMContentLoaded', initI18n);
