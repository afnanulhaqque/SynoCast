
document.addEventListener('DOMContentLoaded', function () {
    var subscribeButton = document.getElementById('navbarSubscribeBtn');
    var subscribeModalEl = document.getElementById('subscribe_modal');
    var subscribeActionBtn = document.getElementById('subscribe-action-btn');
    
    var contactStep = subscribeModalEl?.querySelector('.step-contact');
    var otpStep = subscribeModalEl?.querySelector('.step-otp');
    var successStep = subscribeModalEl?.querySelector('.step-success');
    var errorAlert = subscribeModalEl?.querySelector('#subscribe-error');
    
    var emailInput = document.getElementById('subscriber-email');
    var phoneInput = document.getElementById('subscriber-phone');
    var otpInput = document.getElementById('subscriber-otp');
    var otpInstructions = document.getElementById('otp-instructions');
    
    var methodEmail = document.getElementById('method-email');
    var methodWhatsapp = document.getElementById('method-whatsapp');
    var emailGroup = subscribeModalEl?.querySelector('.input-group-email');
    var whatsappGroup = subscribeModalEl?.querySelector('.input-group-whatsapp');

    var currentContact = null;

    if (!subscribeButton || !subscribeModalEl || !subscribeActionBtn || typeof bootstrap === 'undefined') {
        return;
    }

    var subscribeModal = new bootstrap.Modal(subscribeModalEl);

    function toggleMethod() {
        if (methodEmail.checked) {
            emailGroup.classList.remove('d-none');
            whatsappGroup.classList.add('d-none');
            emailInput.required = true;
            phoneInput.required = false;
        } else {
            emailGroup.classList.add('d-none');
            whatsappGroup.classList.remove('d-none');
            emailInput.required = false;
            phoneInput.required = true;
        }
    }

    function resetModal() {
        contactStep?.classList.remove('d-none');
        otpStep?.classList.add('d-none');
        successStep?.classList.add('d-none');
        errorAlert?.classList.add('d-none');
        errorAlert.textContent = '';
        
        subscribeActionBtn.dataset.state = 'contact';
        subscribeActionBtn.textContent = 'Subscribe';
        subscribeActionBtn.disabled = false;
        
        emailInput.value = '';
        phoneInput.value = '';
        otpInput.value = '';
        currentContact = null;
        
        if (methodEmail) {
            methodEmail.checked = true;
            toggleMethod();
        }
    }

    methodEmail?.addEventListener('change', toggleMethod);
    methodWhatsapp?.addEventListener('change', toggleMethod);

    subscribeModalEl.addEventListener('hidden.bs.modal', resetModal);

    subscribeButton.addEventListener('click', function (event) {
        event.preventDefault();
        resetModal();
        subscribeModal.show();
    });

    subscribeActionBtn.dataset.defaultLabel = 'Subscribe';

    var countryCodeSelect = document.getElementById('country-code');

    async function handleContactSubmit() {
        const isEmail = methodEmail.checked;
        const input = isEmail ? emailInput : phoneInput;
        
        if (!isEmail) {
            const phoneRegex = /^[0-9]{7,15}$/;
            if (!phoneRegex.test(input.value)) {
                errorAlert.textContent = "Enter valid number";
                errorAlert.classList.remove('d-none');
                return;
            }
        }

        if (!input.checkValidity()) {
            input.reportValidity();
            return;
        }

        errorAlert?.classList.add('d-none');
        subscribeActionBtn.dataset.state = 'loading';
        subscribeActionBtn.textContent = 'Sending OTP...';
        subscribeActionBtn.disabled = true;

        const params = new URLSearchParams();
        params.append('action', 'request');
        params.append('type', isEmail ? 'email' : 'whatsapp');
        
        let valueToSend = input.value;
        if (!isEmail && countryCodeSelect) {
            valueToSend = countryCodeSelect.value + input.value;
        }
        params.append(isEmail ? 'email' : 'phone', valueToSend);

        try {
            const response = await fetch('/otp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: params,
            });

            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Unable to send OTP. Please try again.');
            }

            currentContact = isEmail ? data.email : data.phone;
            otpInstructions.textContent = `Enter the 6-digit OTP sent to ${currentContact}.`;
            contactStep.classList.add('d-none');
            otpStep.classList.remove('d-none');
            subscribeActionBtn.dataset.state = 'otp';
            subscribeActionBtn.textContent = 'Verify OTP';
            subscribeActionBtn.disabled = false;
        } catch (error) {
            errorAlert.textContent = error.message;
            errorAlert.classList.remove('d-none');
            subscribeActionBtn.dataset.state = 'contact';
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
        if (state === 'contact' || state === 'email') { // Handle legacy state name just in case
            handleContactSubmit();
        } else if (state === 'otp') {
            handleOtpSubmit();
        } else if (state === 'done') {
            subscribeModal.hide();
        }
    });
});
