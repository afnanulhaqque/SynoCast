/**
 * Global Weather Explorer Logic for Weather Page Tab
 */

const GlobalExplorer = {
    ITEMS_PER_PAGE: 12,
    ALL_CITIES: [],
    filteredCities: [],
    currentPage: 1,
    selectedCountry: "",
    selectedLetter: null,

    init() {
        this.fetchCountries();
        this.setupSearch();
        this.setupCountrySelect();
    },

    async fetchCountries() {
        const select = document.getElementById('ge-countrySelect');
        if (!select) return;

        try {
            const res = await fetch('/assets/data/countries.json');
            const data = await res.json();

            if (data && Array.isArray(data)) {
                const countries = data.sort((a, b) => a.name.localeCompare(b.name));
                countries.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.name;
                    opt.textContent = c.name;
                    select.appendChild(opt);
                });
            }
        } catch (err) {
            console.error("GlobalExplorer: Failed to fetch countries", err);
            select.innerHTML = '<option disabled>Failed to load countries</option>';
        }
    },

    setupCountrySelect() {
        const select = document.getElementById('ge-countrySelect');
        if (!select) return;
        select.addEventListener('change', async (e) => {
            this.selectedCountry = e.target.value;
            await this.fetchCities(this.selectedCountry);
        });
    },

    setupSearch() {
        const searchInput = document.getElementById('ge-citySearch');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            
            if(term.length > 0 && this.selectedLetter) {
                this.selectedLetter = null;
                this.renderAlphabetFilter(); 
            }

            this.filteredCities = this.ALL_CITIES.filter(c => c.toLowerCase().includes(term));
            this.currentPage = 1;
            this.renderPage(this.currentPage);
        });
    },

    async fetchCities(country) {
        if (!country) return;

        this.showLoader(true, `Loading cities in ${country}...`);
        document.getElementById('ge-emptyState').classList.add('d-none');
        document.getElementById('ge-citiesGrid').innerHTML = '';
        document.getElementById('ge-paginationContainer').classList.add('d-none');
        document.getElementById('ge-alphabetRow').classList.add('d-none');
        document.getElementById('ge-citySearch').disabled = true;

        try {
            const csrfToken = document.querySelector('meta[name="_csrf_token"]') ? document.querySelector('meta[name="_csrf_token"]').getAttribute('content') : '';
            const res = await fetch('/api/proxy/cities', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ country: country })
            });

            const json = await res.json();

            if (!res.ok) throw new Error(json.error || 'Failed to fetch');

            if (json.data) {
                this.ALL_CITIES = json.data.sort();
                this.filteredCities = [...this.ALL_CITIES];

                document.getElementById('ge-citySearch').disabled = false;
                document.getElementById('ge-citySearch').value = '';
                this.selectedLetter = null;
                this.currentPage = 1;

                this.showLoader(false);
                
                document.getElementById('ge-alphabetRow').classList.remove('d-none');
                this.renderAlphabetFilter();
                this.renderPage(this.currentPage);
            } else {
                this.showError("No cities found for this country.");
            }
        } catch (err) {
            console.error("GlobalExplorer: Failed to fetch cities", err);
            this.showError("Failed to load cities. Please try again later.");
        }
    },

    renderAlphabetFilter() {
        const container = document.getElementById('ge-alphabetFilter');
        if (!container) return;
        container.innerHTML = '';

        const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
        
        const allBtn = document.createElement('div');
        allBtn.className = `letter-btn ${this.selectedLetter === null ? 'active' : ''}`;
        allBtn.textContent = 'All';
        allBtn.onclick = () => this.filterByLetter(null);
        container.appendChild(allBtn);

        alphabet.forEach(letter => {
            const hasCities = this.ALL_CITIES.some(c => c.toUpperCase().startsWith(letter));
            const btn = document.createElement('div');
            btn.className = `letter-btn ${this.selectedLetter === letter ? 'active' : ''} ${!hasCities ? 'disabled' : ''}`;
            btn.textContent = letter;
            if (hasCities) {
                btn.onclick = () => this.filterByLetter(letter);
            }
            container.appendChild(btn);
        });
    },

    filterByLetter(letter) {
        this.selectedLetter = letter;
        document.getElementById('ge-citySearch').value = '';

        if (letter) {
            this.filteredCities = this.ALL_CITIES.filter(c => c.toUpperCase().startsWith(letter));
        } else {
            this.filteredCities = [...this.ALL_CITIES];
        }

        this.renderAlphabetFilter();
        this.currentPage = 1;
        this.renderPage(this.currentPage);
    },

    renderPage(page) {
        const grid = document.getElementById('ge-citiesGrid');
        const paginationContainer = document.getElementById('ge-paginationContainer');
        if (!grid || !paginationContainer) return;

        grid.innerHTML = '';

        if (this.filteredCities.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center text-muted"><p>No cities found matching your criteria.</p></div>';
            paginationContainer.classList.add('d-none');
            return;
        }

        paginationContainer.classList.remove('d-none');

        const start = (page - 1) * this.ITEMS_PER_PAGE;
        const end = start + this.ITEMS_PER_PAGE;
        const pageCities = this.filteredCities.slice(start, end);

        pageCities.forEach(city => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4';
            const safeId = `ge-card-${city.replace(/[^a-zA-Z0-9-]/g, '-')}-${Math.random().toString(36).substr(2, 9)}`;
            col.id = safeId;
            col.innerHTML = `
                <div class="card city-card p-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h5 class="card-title fw-bold mb-1 text-truncate" style="max-width: 200px;" title="${city}">${city}</h5>
                            <small class="text-muted"><i class="fas fa-globe me-1"></i> ${this.selectedCountry}</small>
                        </div>
                        <div class="loading-skeleton" style="width:50px; height:50px; border-radius:50%"></div>
                    </div>
                    <div class="mt-3 text-center">
                         <div class="loading-skeleton mx-auto mb-2" style="width:100px; height:40px;"></div>
                         <div class="loading-skeleton mx-auto" style="width:150px; height:20px;"></div>
                    </div>
                </div>
            `;
            grid.appendChild(col);
            this.fetchWeather(city, safeId);
        });

        this.renderPagination(Math.ceil(this.filteredCities.length / this.ITEMS_PER_PAGE));
    },

    async fetchWeather(city, cardId) {
        try {
            const query = `${city},${this.selectedCountry}`;
            const res = await fetch(`/api/travel/weather?q=${encodeURIComponent(query)}`);

            if (!res.ok) throw new Error('Weather data unavailable');

            const data = await res.json();
            this.updateCard(cardId, data, city);
        } catch (err) {
            const card = document.getElementById(cardId);
            if (card) {
                card.querySelector('.city-card').innerHTML = `
                     <div class="p-3 text-center">
                        <h5 class="fw-bold text-muted">${city}</h5>
                        <p class="text-danger small mb-0"><i class="fas fa-exclamation-circle"></i> Unavailable</p>
                    </div>
                `;
            }
        }
    },

    updateCard(cardId, data, originalCity) {
        const cardContainer = document.getElementById(cardId);
        if (!cardContainer) return;

        const iconUrl = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;

        cardContainer.innerHTML = `
            <div class="card city-card p-3 h-100">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="card-title fw-bold mb-0 text-truncate" style="max-width: 180px;" title="${originalCity}">${originalCity}</h5>
                        <p class="card-text text-muted small mb-0 text-capitalize">${data.condition}</p>
                    </div>
                    <img src="${iconUrl}" alt="${data.condition}" class="weather-icon-large">
                </div>
                <div class="d-flex justify-content-between align-items-end mt-3">
                    <div class="temp-large">${Math.round(data.temp)}°</div>
                    <div class="text-end text-muted small">
                        <div><i class="fas fa-wind me-1"></i> ${data.wind_speed} m/s</div>
                        <div><i class="fas fa-tint me-1"></i> ${data.humidity}%</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderPagination(totalPages) {
        const pag = document.getElementById('ge-pagination');
        if (!pag) return;
        pag.innerHTML = '';

        if (totalPages <= 1) return;

        const addItem = (page, text, disabled = false, active = false) => {
            const li = document.createElement('li');
            li.className = `page-item ${disabled ? 'disabled' : ''} ${active ? 'active' : ''}`;
            const html = `<a class="page-link" href="#" onclick="GlobalExplorer.changePage(${page}); return false;">${text}</a>`;
            li.innerHTML = html;
            pag.appendChild(li);
        };

        addItem(this.currentPage - 1, '&laquo;', this.currentPage === 1);

        let startPage = Math.max(1, this.currentPage - 2);
        let endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            addItem(1, '1', false, 1 === this.currentPage);
            if (startPage > 2) addItem(0, '...', true);
        }

        for (let i = startPage; i <= endPage; i++) {
            addItem(i, i, false, i === this.currentPage);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) addItem(0, '...', true);
            addItem(totalPages, totalPages, false, totalPages === this.currentPage);
        }

        addItem(this.currentPage + 1, '&raquo;', this.currentPage === totalPages);
    },

    changePage(page) {
        const totalPages = Math.ceil(this.filteredCities.length / this.ITEMS_PER_PAGE);
        if (page < 1 || page > totalPages) return;
        this.currentPage = page;
        this.renderPage(page);
        
        const grid = document.getElementById('ge-citiesGrid');
        if (grid) {
            const yOffset = -150; 
            const y = grid.getBoundingClientRect().top + window.pageYOffset + yOffset;
            window.scrollTo({ top: y, behavior: 'smooth' });
        }
    },

    showLoader(show, text = 'Loading...') {
        const loader = document.getElementById('ge-loader');
        const loaderText = document.getElementById('ge-loaderText');
        if (!loader) return;
        
        if (show) {
            loader.classList.remove('d-none');
            if (loaderText) loaderText.textContent = text;
        } else {
            loader.classList.add('d-none');
        }
    },

    showError(msg) {
        this.showLoader(false);
        const grid = document.getElementById('ge-citiesGrid');
        if (grid) grid.innerHTML = `<div class="col-12 text-center text-danger"><p>${msg}</p></div>`;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // We init this when the tab is clicked, or just init it and let it sit there.
    // For now, let's just init it.
    GlobalExplorer.init();
});
