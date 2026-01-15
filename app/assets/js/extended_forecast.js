// Extended Forecast Functionality
// This code should be added to weather.js

// ===== ADD THIS TO THE TOP OF weather.js (after line 6, with other state variables) =====
let extendedData = null; // Store extended forecast data

// ===== ADD THIS AFTER LINE 631 (after forecastAnalyticsEl declaration) =====
const tabExtended = document.getElementById('tab-extended');
const forecastExtendedEl = document.getElementById('forecast-extended');

// ===== MODIFY switchTab function (around line 638) to include 'extended' case =====
// Add this to the resetTab calls (around line 649):
resetTab(tabExtended);

// Add this to the classList.add('d-none') calls (around line 653):
forecastExtendedEl?.classList.add('d-none');

// Add this new else-if block after the 'analytics' case (around line 680):
/*
} else if (tab === 'extended') {
    forecastExtendedEl?.classList.remove('d-none');
    if (tabExtended) {
        tabExtended.classList.remove('text-muted');
        tabExtended.classList.add('text-dark');
        tabExtended.style.opacity = '1';
    }
    if (currentData) {
        // Fetch extended forecast data
        fetchExtendedForecast(currentData.coord.lat, currentData.coord.lon);
    }
}
*/

// ===== ADD THIS AFTER LINE 685 (after tab event listeners) =====
if (tabExtended) tabExtended.addEventListener('click', () => switchTab('extended'));

// ===== ADD THESE FUNCTIONS AT THE END OF THE FILE (before the closing }); around line 1138) =====

// --- Extended Forecast Functions ---

async function fetchExtendedForecast(lat, lon) {
    if (!lat || !lon) return;
    
    try {
        const response = await fetch(`/api/weather/extended?lat=${lat}&lon=${lon}`);
        if (!response.ok) throw new Error('Extended forecast API failed');
        const data = await response.json();
        
        extendedData = data;
        
        // Show note if simulated
        const noteEl = document.getElementById('extended-note');
        if (noteEl && data.note) {
            noteEl.classList.remove('d-none');
        } else if (noteEl) {
            noteEl.classList.add('d-none');
        }
        
        // Render sections
        renderExtendedDaily(data.daily);
        renderExtendedHourly(data.hourly);
        renderAstronomy(data.daily);
        
    } catch (error) {
        console.error('Extended forecast error:', error);
        const dailyEl = document.getElementById('extended-daily-forecast');
        if (dailyEl) {
            dailyEl.innerHTML = '<div class="text-center py-5 w-100"><p class="text-danger">Failed to load extended forecast</p></div>';
        }
    }
}

function renderExtendedDaily(dailyData) {
    const container = document.getElementById('extended-daily-forecast');
    if (!container || !dailyData) return;
    
    container.innerHTML = '';
    
    dailyData.forEach((day, index) => {
        const iconClass = WeatherUtils.getIconClass(
            day.weather.icon.includes('d') ? 800 : 801, 
            day.weather.icon
        );
        
        const tempMax = Math.round(day.temp.max);
        const tempMin = Math.round(day.temp.min);
        
        const isSimulated = day.simulated ? 'opacity-75' : '';
        const simulatedBadge = day.simulated ? '<span class="badge bg-secondary-subtle text-secondary small">Est.</span>' : '';
        
        const card = document.createElement('div');
        card.className = `card border-0 rounded-4 p-3 flex-shrink-0 ${isSimulated}`;
        card.style = `width: 180px; border: 1px solid #eee;`;
        card.innerHTML = `
            <div class="card-body p-0">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <p class="small fw-bold mb-0">${day.date}</p>
                    ${simulatedBadge}
                </div>
                <p class="small text-muted mb-3 text-capitalize">${day.weather.description}</p>
                
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <div>
                        <div class="d-flex align-items-center gap-1 mb-1">
                            <i class="fas fa-arrow-up text-danger small"></i>
                            <span class="temp-display fw-bold" data-celsius="${tempMax}">${tempMax}°</span>
                        </div>
                        <div class="d-flex align-items-center gap-1">
                            <i class="fas fa-arrow-down text-primary small"></i>
                            <span class="temp-display" data-celsius="${tempMin}">${tempMin}°</span>
                        </div>
                    </div>
                    <i class="fas ${iconClass} fa-3x text-muted"></i>
                </div>
                
                <div class="d-flex justify-content-between small text-muted">
                    <span><i class="fas fa-tint me-1"></i>${day.pop}%</span>
                    <span><i class="fas fa-wind me-1"></i>${day.wind_speed}km/h</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
    
    // Update temperature units
    updateDisplayUnits();
}

function renderExtendedHourly(hourlyData) {
    const container = document.getElementById('extended-hourly-forecast');
    if (!container || !hourlyData) return;
    
    container.innerHTML = '';
    
    hourlyData.forEach((hour, index) => {
        const iconClass = WeatherUtils.getIconClass(
            hour.weather.icon.includes('d') ? 800 : 801,
            hour.weather.icon
        );
        
        const temp = Math.round(hour.temp);
        
        // Group by day
        const showDate = index === 0 || hour.date !== hourlyData[index - 1]?.date;
        
        const card = document.createElement('div');
        card.className = 'card border-0 rounded-4 p-3 flex-shrink-0';
        card.style = `width: 140px; border: 1px solid #eee;`;
        card.innerHTML = `
            <div class="card-body p-0">
                ${showDate ? `<p class="small text-muted mb-1">${hour.date}</p>` : ''}
                <p class="small fw-bold mb-2">${hour.time}</p>
                
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div>
                        <div class="d-flex align-items-center gap-1 mb-1">
                            <i class="fas fa-thermometer-half text-primary small"></i>
                            <span class="temp-display fw-bold" data-celsius="${temp}">${temp}°</span>
                        </div>
                        <div class="small text-muted">
                            <i class="fas fa-tint me-1"></i>${hour.pop}%
                        </div>
                    </div>
                    <i class="fas ${iconClass} fa-2x text-muted"></i>
                </div>
                
                <p class="small text-muted text-capitalize mb-0">${hour.weather.description}</p>
            </div>
        `;
        container.appendChild(card);
    });
    
    // Update temperature units
    updateDisplayUnits();
}

function renderAstronomy(dailyData) {
    if (!dailyData || !dailyData[0]) return;
    
    // Render Sunrise/Sunset with Golden Hours
    renderSunData(dailyData);
    
    // Render Moon Phases
    renderMoonPhases(dailyData);
}

function renderSunData(dailyData) {
    const container = document.getElementById('astronomy-sun-data');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Show first 3 days
    dailyData.slice(0, 3).forEach((day, index) => {
        if (!day.astronomy) return;
        
        const astro = day.astronomy;
        const goldenHours = astro.golden_hours;
        
        const dayCard = document.createElement('div');
        dayCard.className = index < 2 ? 'mb-4 pb-3 border-bottom' : 'mb-2';
        dayCard.innerHTML = `
            <p class="small fw-bold mb-2">${day.date}</p>
            
            <div class="row g-2 mb-3">
                <div class="col-6">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fas fa-sunrise text-warning"></i>
                        <div>
                            <div class="small text-muted">Sunrise</div>
                            <div class="fw-bold">${astro.sunrise}</div>
                        </div>
                    </div>
                </div>
                <div class="col-6">
                    <div class="d-flex align-items-center gap-2">
                        <i class="fas fa-sunset text-warning"></i>
                        <div>
                            <div class="small text-muted">Sunset</div>
                            <div class="fw-bold">${astro.sunset}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            ${goldenHours ? `
                <div class="bg-warning-subtle p-2 rounded-3">
                    <div class="small fw-bold text-warning-emphasis mb-1">
                        <i class="fas fa-camera me-1"></i>Golden Hours
                    </div>
                    <div class="row g-2 small">
                        <div class="col-6">
                            <div class="text-muted">Morning</div>
                            <div>${goldenHours.morning.start} - ${goldenHours.morning.end}</div>
                        </div>
                        <div class="col-6">
                            <div class="text-muted">Evening</div>
                            <div>${goldenHours.evening.start} - ${goldenHours.evening.end}</div>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
        container.appendChild(dayCard);
    });
}

function renderMoonPhases(dailyData) {
    const container = document.getElementById('astronomy-moon-calendar');
    if (!container) return;
    
    container.innerHTML = '';
    
    dailyData.forEach((day, index) => {
        if (!day.astronomy || !day.astronomy.moon_phase) return;
        
        const moonPhase = day.astronomy.moon_phase;
        
        const phaseCard = document.createElement('div');
        phaseCard.className = index < dailyData.length - 1 ? 'mb-3 pb-2 border-bottom' : 'mb-2';
        phaseCard.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <p class="small text-muted mb-0">${day.date}</p>
                    <p class="fw-bold mb-0">${moonPhase.name}</p>
                    <p class="small text-muted mb-0">${moonPhase.illumination}</p>
                </div>
                <div class="fs-1">${moonPhase.emoji}</div>
            </div>
        `;
        container.appendChild(phaseCard);
    });
}

