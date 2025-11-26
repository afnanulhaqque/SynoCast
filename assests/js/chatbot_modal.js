// Simple chatbot modal logic
document.addEventListener('DOMContentLoaded', function () {
    const modalEl = document.getElementById('chatbot_modal');
    const messagesEl = document.getElementById('chatbot_messages');
    const form = document.getElementById('chatbot_form');
    const input = document.getElementById('chatbot_input');

    // Helper: append message
    function appendMessage(sender, text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'message ' + (sender === 'user' ? 'user' : 'bot');
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;
        wrapper.appendChild(bubble);
        messagesEl.appendChild(wrapper);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    // Focus input when modal opens
    const bsModalEl = document.getElementById('chatbot_modal');
    if (bsModalEl) {
        bsModalEl.addEventListener('shown.bs.modal', function () {
            input.focus();
            // show a friendly greeting when opened
            // clear old messages and show greeting
            messagesEl.innerHTML = '';
            appendMessage('bot', "Hello! I'm SynoCast — ask me about weather, news, or the site.");
        });
    }

    // Submit handler
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const value = input.value && input.value.trim();
            if (!value) return;
            appendMessage('user', value);

            // POST to /chat (server endpoint) expecting JSON reply with {reply: string}
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: value })
            })
                .then(r => r.json())
                .then(data => {
                    appendMessage('bot', data.reply || "Sorry, I couldn't answer that.");
                })
                .catch(err => {
                    appendMessage('bot', 'Sorry, an error occurred.');
                    console.error('chat error', err);
                });

            input.value = '';
            input.focus();
        });
    }
});
