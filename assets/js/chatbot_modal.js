document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('chatbot_modal');
    const messagesEl = document.getElementById('chatbot_messages');
    const form = document.getElementById('chatbot_form');
    const input = document.getElementById('chatbot_input');
    const typingIndicator = document.getElementById('modal-typing-indicator');
    const chips = document.querySelectorAll('#modal-example-questions .suggestion-chip');

    // Helper: append message
    function appendMessage(sender, text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message ' + (sender === 'user' ? 'user' : 'bot');
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        
        // Simple markdown-like parsing for bold text
        if (sender === 'bot') {
            const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            bubble.innerHTML = formattedText;
        } else {
            bubble.textContent = text;
        }

        wrapper.appendChild(bubble);
        
        // Insert before typing indicator if it exists and is visible, otherwise append
        if (typingIndicator && typingIndicator.parentNode === messagesEl) {
            messagesEl.insertBefore(wrapper, typingIndicator);
        } else {
            messagesEl.appendChild(wrapper);
        }
        
        scrollToBottom();
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function showTyping() {
        if (typingIndicator) {
            typingIndicator.style.display = 'block';
            // Move to bottom
            messagesEl.appendChild(typingIndicator);
            scrollToBottom();
        }
    }

    function hideTyping() {
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }

    async function sendMessage(message) {
        if (!message || !message.trim()) return;

        appendMessage('user', message);
        input.value = '';
        showTyping();

        const payload = { message: message };

        if (navigator.geolocation) {
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
                });
                payload.lat = position.coords.latitude;
                payload.lon = position.coords.longitude;
            } catch (geoErr) {
                // Silently fallback to IP-based detection on backend
            }
        }

        try {
            const response = await fetch('/api/ai_chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': SecurityUtils.getCsrfToken()
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            hideTyping();

            if (data.error) {
                appendMessage('bot', "Sorry, I encountered an error: " + data.error);
            } else {
                appendMessage('bot', data.reply || "Sorry, I couldn't answer that.");
            }
        } catch (err) {
            hideTyping();
            appendMessage('bot', "Sorry, I couldn't connect to the server.");
        }
    }

    // Event Listeners

    // Focus input when modal opens
    if (modalEl) {
        modalEl.addEventListener('shown.bs.modal', function () {
            input.focus();
            // Show greeting if empty (excluding typing indicator)
            const messages = messagesEl.querySelectorAll('.message');
            if (messages.length === 0) {
                appendMessage('bot', "Hello! I'm SynoCast — ask me about weather, news, or the site.");
            }
        });
    }

    // Submit handler
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            sendMessage(input.value);
        });
    }

    // Chip handlers
    chips.forEach(chip => {
        chip.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            sendMessage(question);
        });
    });
});
