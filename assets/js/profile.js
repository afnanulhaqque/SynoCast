document.addEventListener('DOMContentLoaded', function() {
    
    // --- Elements ---
    const profileForm = document.getElementById('profile-form');
    const saveSpinner = document.getElementById('save-spinner');
    const saveMessage = document.getElementById('save-message');
    const btnLogout = document.getElementById('btn-logout');

    // --- Logout Logic ---
    if (btnLogout) {
        btnLogout.addEventListener('click', async function() {
            if (!confirm('Are you sure you want to log out?')) return;
            
            try {
                const res = await fetch('/api/user/logout', { 
                    method: 'POST',
                    headers: { 'X-CSRFToken': SecurityUtils.getCsrfToken() }
                });
                if (res.ok) {
                    window.location.href = '/';
                }
            } catch (e) {
                console.error("Logout failed:", e);
            }
        });
    }

    // --- Profile Preferences Form ---
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Get Data
            const formData = new FormData(profileForm);
            
            // Temp Unit
            const tempUnit = formData.get('tempUnit');
            
            // Activities (checkboxes)
            const activities = [];
            document.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
                if (cb.id.startsWith('act-')) {
                    activities.push(cb.value);
                }
            });

            // Dashboard Widgets
            const dashboardConfig = {
                show_news: document.getElementById('widget-news').checked,
                show_map: document.getElementById('widget-map').checked
            };

            // UI Feedback
            const submitBtn = profileForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            saveSpinner.classList.remove('d-none');
            
            try {
                const response = await fetch('/api/user/profile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': SecurityUtils.getCsrfToken()
                    },
                    body: JSON.stringify({
                        temperature_unit: tempUnit,
                        activities: activities,
                        dashboard_config: dashboardConfig
                    })
                });

                if (response.ok) {
                    // Show success
                    saveMessage.classList.remove('opacity-0');
                    setTimeout(() => saveMessage.classList.add('opacity-0'), 2000);
                } else {
                    alert('Failed to save settings. Please try again.');
                }
            } catch (err) {
                console.error(err);
                alert('An error occurred.');
            } finally {
                submitBtn.disabled = false;
                saveSpinner.classList.add('d-none');
            }
        });
    }

    // --- Delete Favorites ---
    document.querySelectorAll('.btn-delete-fav').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            // Prevent Card Click
            e.stopPropagation(); 
            
            if (!confirm('Remove this location from favorites?')) return;
            
            const favId = this.dataset.id;
            const listItem = this.closest('.list-group-item');
            
            try { // Assuming SecurityUtils is globally available from weather_utils.js or base
                const res = await fetch(`/api/user/favorites?id=${favId}`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': SecurityUtils.getCsrfToken() }
                });
                
                if (res.ok) {
                    listItem.remove();
                    // If empty, show empty state (optional, simplified here)
                    if (document.querySelectorAll('.list-group-item').length === 0) {
                        location.reload(); 
                    }
                }
            } catch (err) {
                console.error("Delete failed:", err);
            }
        });
    });

});
