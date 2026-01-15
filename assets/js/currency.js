/**
 * SynoCast Currency Management Utility
 * Handles currency formatting, conversion, and travel cost insights.
 */

class CurrencyManager {
    constructor() {
        this.baseCurrency = 'USD';
        this.userCurrency = localStorage.getItem('synocast_currency') || 'USD';
        this.rates = {};
    }

    async init() {
        // Fetch rates from backend or use local storage if available
        await this.fetchRates();
        this.applyCurrencyFormatting();
        
        window.addEventListener('languageChanged', () => this.applyCurrencyFormatting());
    }

    async fetchRates() {
        try {
            // We can add an API endpoint specifically for rates if needed, 
            // but for now we fetch it through a generic preferences call or a dedicated rates endpoint.
            const response = await fetch('/api/currency/rates');
            if (response.ok) {
                const data = await response.json();
                this.rates = data.rates;
            } else {
                // Default fallback rates
                this.rates = { "USD": 1, "EUR": 0.92, "GBP": 0.79, "JPY": 150.25, "CNY": 7.21, "PKR": 278.5 };
            }
        } catch (error) {
            console.error('Failed to fetch rates:', error);
        }
    }

    setCurrency(curr) {
        this.userCurrency = curr;
        localStorage.setItem('synocast_currency', curr);
        this.applyCurrencyFormatting();
        this.savePreferenceToBackend(curr);
        
        window.dispatchEvent(new CustomEvent('currencyChanged', { detail: { currency: curr } }));
    }

    async savePreferenceToBackend(curr) {
        try {
            await fetch('/api/user/profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ currency: curr })
            });
        } catch (e) { /* ignore */ }
    }

    format(amount, currency = null) {
        const curr = currency || this.userCurrency;
        return new Intl.NumberFormat(document.documentElement.lang || 'en', {
            style: 'currency',
            currency: curr
        }).format(amount);
    }

    applyCurrencyFormatting() {
        const elements = document.querySelectorAll('[data-amount]');
        elements.forEach(el => {
            const amount = parseFloat(el.getAttribute('data-amount'));
            const fromCurr = el.getAttribute('data-from-currency') || 'USD';
            
            if (!isNaN(amount)) {
                // Convert if necessary (simple client-side conversion)
                let converted = amount;
                if (fromCurr !== this.userCurrency && this.rates[fromCurr] && this.rates[this.userCurrency]) {
                    const amountUSD = amount / this.rates[fromCurr];
                    converted = amountUSD * this.rates[this.userCurrency];
                }
                
                el.textContent = this.format(converted);
            }
        });
    }
}

// Global instance
const currencyManager = new CurrencyManager();
document.addEventListener('DOMContentLoaded', () => currencyManager.init());
