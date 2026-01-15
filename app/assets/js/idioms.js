/**
 * SynoCast Weather Idioms Utility
 * Displays culturally relevant weather sayings based on current conditions.
 */

class IdiomManager {
    constructor() {
        this.idioms = {};
    }

    async init() {
        try {
            const response = await fetch('/assets/idioms.json');
            this.idioms = await response.json();
            
            // Re-render when weather data is loaded or condition changes
            window.addEventListener('weatherDataLoaded', (e) => this.displayIdiom(e.detail.condition));
            window.addEventListener('languageChanged', () => this.refreshIdiom());
        } catch (error) {
            console.error('Failed to load idioms:', error);
        }
    }

    displayIdiom(condition) {
        this.currentCondition = condition.toLowerCase();
        this.refreshIdiom();
    }

    refreshIdiom() {
        if (!this.currentCondition || !this.idioms) return;

        const lang = document.documentElement.lang || 'en';
        let pool = this.idioms[this.currentCondition] || [];
        
        // If no idioms for condition, try "clear" or generic
        if (pool.length === 0) {
            pool = this.idioms['clear'] || [];
        }

        // Filter by language or show English as fallback
        let relevantIdioms = pool.filter(i => i.language === lang);
        if (relevantIdioms.length === 0) {
            relevantIdioms = pool.filter(i => i.language === 'en');
        }

        if (relevantIdioms.length > 0) {
            const idiom = relevantIdioms[Math.floor(Math.random() * relevantIdioms.length)];
            this.updateUI(idiom);
        }
    }

    updateUI(idiomData) {
        const containers = document.querySelectorAll('.weather-idiom-container');
        containers.forEach(container => {
            const textEl = container.querySelector('.idiom-text');
            const meaningEl = container.querySelector('.idiom-meaning');
            const contextEl = container.querySelector('.idiom-context');

            if (textEl) textEl.textContent = `"${idiomData.idiom}"`;
            if (meaningEl) meaningEl.textContent = idiomData.meaning;
            if (contextEl) contextEl.textContent = idiomData.context;

            container.classList.remove('d-none');
            container.classList.add('fade-in');
        });
    }
}

// Global instance
const idiomManager = new IdiomManager();
document.addEventListener('DOMContentLoaded', () => idiomManager.init());
