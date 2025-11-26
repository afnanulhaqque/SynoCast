
document.addEventListener('DOMContentLoaded', function () {
    var subscribeButton = document.getElementById('navbarSubscribeBtn');
    var subscribeModalEl = document.getElementById('subscribe_modal');
    var subscribeActionBtn = document.getElementById('subscribe-action-btn');
    var emailStep = subscribeModalEl?.querySelector('.step-email');
    var otpStep = subscribeModalEl?.querySelector('.step-otp');
    var successStep = subscribeModalEl?.querySelector('.step-success');
    var errorAlert = subscribeModalEl?.querySelector('#subscribe-error');
    var emailInput = document.getElementById('subscriber-email');
    var otpInput = document.getElementById('subscriber-otp');
    var otpInstructions = document.getElementById('otp-instructions');
    var currentEmail = null;

    if (!subscribeButton || !subscribeModalEl || !subscribeActionBtn || typeof bootstrap === 'undefined') {
        return;
    }

    var subscribeModal = new bootstrap.Modal(subscribeModalEl);

    function resetModal() {
        emailStep?.classList.remove('d-none');
        otpStep?.classList.add('d-none');
        successStep?.classList.add('d-none');
        errorAlert?.classList.add('d-none');
        errorAlert.textContent = '';
        subscribeActionBtn.dataset.state = 'email';
        subscribeActionBtn.textContent = 'Subscribe';
        subscribeActionBtn.disabled = false;
        emailInput.value = '';
        otpInput.value = '';
        currentEmail = null;
    }

    subscribeModalEl.addEventListener('hidden.bs.modal', resetModal);

    subscribeButton.addEventListener('click', function (event) {
        event.preventDefault();
        resetModal();
        subscribeModal.show();
    });

    function setLoading(isLoading) {
        subscribeActionBtn.disabled = isLoading;
        subscribeActionBtn.textContent = isLoading ? 'Please wait...' : subscribeActionBtn.dataset.defaultLabel;
    }

    subscribeActionBtn.dataset.defaultLabel = 'Subscribe';

    async function handleEmailSubmit() {
        if (!emailInput.checkValidity()) {
            emailInput.reportValidity();
            return;
        }

        errorAlert?.classList.add('d-none');
        subscribeActionBtn.dataset.state = 'loading';
        subscribeActionBtn.textContent = 'Sending OTP...';
        subscribeActionBtn.disabled = true;

        try {
            const response = await fetch('/otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    action: 'request',
                    email: emailInput.value,
                }),
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Unable to send OTP. Please try again.');
            }

            currentEmail = data.email;
            otpInstructions.textContent = `Enter the 6-digit OTP sent to ${currentEmail}.`;
            emailStep.classList.add('d-none');
            otpStep.classList.remove('d-none');
            subscribeActionBtn.dataset.state = 'otp';
            subscribeActionBtn.textContent = 'Verify OTP';
            subscribeActionBtn.disabled = false;
        } catch (error) {
            errorAlert.textContent = error.message;
            errorAlert.classList.remove('d-none');
            subscribeActionBtn.dataset.state = 'email';
            subscribeActionBtn.textContent = 'Subscribe';
            subscribeActionBtn.disabled = false;
        }
    }

    async function handleOtpSubmit() {
        if (!otpInput.checkValidity()) {
            otpInput.reportValidity();
            return;
        }

        errorAlert?.classList.add('d-none');
        subscribeActionBtn.dataset.state = 'loading';
        subscribeActionBtn.textContent = 'Verifying...';
        subscribeActionBtn.disabled = true;

        try {
            const response = await fetch('/otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    action: 'verify',
                    otp: otpInput.value,
                }),
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Incorrect OTP.');
            }

            otpStep.classList.add('d-none');
            successStep.classList.remove('d-none');
            subscribeActionBtn.dataset.state = 'done';
            subscribeActionBtn.textContent = 'Done';
            subscribeActionBtn.disabled = false;
        } catch (error) {
            errorAlert.textContent = error.message;
            errorAlert.classList.remove('d-none');
            subscribeActionBtn.dataset.state = 'otp';
            subscribeActionBtn.textContent = 'Verify OTP';
            subscribeActionBtn.disabled = false;
        }
    }

    subscribeActionBtn.addEventListener('click', function () {
        const state = subscribeActionBtn.dataset.state;
        if (state === 'email') {
            handleEmailSubmit();
        } else if (state === 'otp') {
            handleOtpSubmit();
        } else if (state === 'done') {
            subscribeModal.hide();
        }
    });
});

