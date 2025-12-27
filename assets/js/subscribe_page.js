document.addEventListener('DOMContentLoaded', function () {
    // Cache DOM elements
    const steps = {
        contact: document.getElementById('step-contact'),
        prefs: document.getElementById('step-prefs'),
        otp: document.getElementById('step-otp'),
        success: document.getElementById('step-success')
    };

    const inputs = {
        email: document.getElementById('page-email'),
        otp: document.getElementById('page-otp-input'),
        severity: document.getElementById('pref-severity'),
        checks: {
            severe: document.getElementById('pref-severe'),
            rain: document.getElementById('pref-rain'),
            temp: document.getElementById('pref-temp'),
            air: document.getElementById('pref-air')
        }
    };

    const buttons = {
        nextPrefs: document.getElementById('btn-next-prefs'),
        backContact: document.getElementById('btn-back-contact'),
        sendOtp: document.getElementById('btn-send-otp'),
        backPrefs: document.getElementById('btn-back-prefs'),
        verifyOtp: document.getElementById('btn-verify-otp'),
        enablePush: document.getElementById('btn-enable-push')
    };

    const errorAlert = document.getElementById('page-error');
    const otpInstructions = document.getElementById('page-otp-instructions');

    let currentEmail = '';

    // Helpers
    function showStep(stepName) {
        Object.values(steps).forEach(el => el.classList.add('d-none'));
        steps[stepName].classList.remove('d-none');
        errorAlert.classList.add('d-none');
    }

    function showError(msg) {
        errorAlert.textContent = msg;
        errorAlert.classList.remove('d-none');
    }

    function urlBase64ToUint8Array(base64String) {
      const padding = '='.repeat((4 - base64String.length % 4) % 4);
      const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');
      const rawData = window.atob(base64);
      const outputArray = new Uint8Array(rawData.length);
      for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
      }
      return outputArray;
    }

    async function registerPush() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            showError('Push notifications are not supported on this browser.');
            return;
        }

        try {
           buttons.enablePush.disabled = true;
           buttons.enablePush.textContent = 'Enabling...';
           
           const registration = await navigator.serviceWorker.ready;
           
           // Get Public Key
           const keyRes = await fetch('/api/push/vapid-public-key');
           const keyData = await keyRes.json();
           const applicationServerKey = urlBase64ToUint8Array(keyData.publicKey);
           
           const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });
            
            // Send to Backend
            // We need lat/lon - try to get from session or browser
            // For now, let's assume session or basic 'ask'
            let location = { lat: null, lon: null };
            // Try simple geolocation
            if (navigator.geolocation) {
                 try {
                     const pos = await new Promise((resolve, reject) => 
                        navigator.geolocation.getCurrentPosition(resolve, reject, {timeout: 5000}));
                     location.lat = pos.coords.latitude;
                     location.lon = pos.coords.longitude;
                 } catch (e) { console.log('Location denied for push', e); }
            }

            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SecurityUtils.getCsrfToken()
                },
                body: JSON.stringify({
                    subscription: subscription,
                    location: location
                })
            });

            buttons.enablePush.textContent = 'Enabled ✓';
            buttons.enablePush.classList.replace('btn-outline-primary', 'btn-success');
            
        } catch (err) {
            console.error(err);
            showError('Failed to enable notifications. Blocked?');
            buttons.enablePush.disabled = false;
            buttons.enablePush.textContent = 'Enable';
        }
    }

    buttons.enablePush.addEventListener('click', registerPush);

    function getPreferences() {
        const selectedTypes = [];
        if (inputs.checks.severe.checked) selectedTypes.push('severe');
        if (inputs.checks.rain.checked) selectedTypes.push('rain');
        if (inputs.checks.temp.checked) selectedTypes.push('temp');
        if (inputs.checks.air.checked) selectedTypes.push('air');

        return {
            severity: inputs.severity.value,
            types: selectedTypes
        };
    }

    // Navigation Events
    buttons.nextPrefs.addEventListener('click', () => {
        if (!inputs.email.checkValidity() || !inputs.email.value) {
            inputs.email.reportValidity();
            return;
        }
        currentEmail = inputs.email.value;
        showStep('prefs');
    });

    buttons.backContact.addEventListener('click', () => showStep('contact'));
    buttons.backPrefs.addEventListener('click', () => showStep('prefs'));

    // API Handling
    buttons.sendOtp.addEventListener('click', async () => {
        buttons.sendOtp.disabled = true;
        buttons.sendOtp.textContent = 'Sending...';
        errorAlert.classList.add('d-none');

        const params = new URLSearchParams();
        params.append('action', 'request');
        params.append('type', 'email');
        params.append('email', currentEmail);
        
        // Pass preferences as JSON string
        const prefs = getPreferences();
        params.append('preferences', JSON.stringify(prefs));

        try {
            const response = await fetch('/otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': SecurityUtils.getCsrfToken() // Assuming SecurityUtils is available via base.html/utils
                },
                body: params
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Failed to send OTP');
            }

            otpInstructions.textContent = `Enter the 6-digit code sent to ${currentEmail}`;
            showStep('otp');
        } catch (err) {
            showError(err.message);
        } finally {
            buttons.sendOtp.disabled = false;
            buttons.sendOtp.textContent = 'Send Verification Code';
        }
    });

    buttons.verifyOtp.addEventListener('click', async () => {
        if (!inputs.otp.value || inputs.otp.value.length !== 6) {
            showError('Please enter a valid 6-digit OTP.');
            return;
        }

        buttons.verifyOtp.disabled = true;
        buttons.verifyOtp.textContent = 'Verifying...';
        errorAlert.classList.add('d-none');

        try {
            const response = await fetch('/otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': SecurityUtils.getCsrfToken()
                },
                body: new URLSearchParams({
                    action: 'verify',
                    otp: inputs.otp.value
                })
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Incorrect OTP');
            }

            showStep('success');
        } catch (err) {
            showError(err.message);
        } finally {
            buttons.verifyOtp.disabled = false;
            buttons.verifyOtp.textContent = 'Verify & Subscribe';
        }
    });
});
