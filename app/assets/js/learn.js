
document.addEventListener('DOMContentLoaded', () => {

    // --- Trivia Logic ---
    const triviaQuestion = document.getElementById('trivia-question');
    const triviaOptions = document.getElementById('trivia-options');
    const triviaResult = document.getElementById('trivia-result');
    const nextBtn = document.getElementById('next-trivia-btn');

    let currentQuestion = null;

    async function loadTrivia() {
        // Reset UI
        triviaResult.classList.add('d-none');
        triviaOptions.innerHTML = '<div class="placeholder-glow"><span class="placeholder col-12 py-3 rounded"></span></div>';
        
        try {
            const res = await fetch('/api/learn/trivia');
            currentQuestion = await res.json();
            
            renderQuestion(currentQuestion);

        } catch (e) {
            triviaQuestion.textContent = "Failed to load trivia.";
        }
    }

    function renderQuestion(q) {
        triviaQuestion.textContent = q.q;
        triviaOptions.innerHTML = '';
        
        q.options.forEach((opt, idx) => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-outline-light text-start fw-bold py-2 px-3 border-2 rounded-3';
            btn.textContent = opt;
            btn.onclick = () => checkAnswer(idx);
            triviaOptions.appendChild(btn);
        });
    }

    function checkAnswer(selectedIndex) {
        const btns = triviaOptions.querySelectorAll('button');
        const isCorrect = selectedIndex === currentQuestion.a;
        
        btns.forEach((btn, idx) => {
            btn.disabled = true;
            if (idx === currentQuestion.a) {
                btn.classList.remove('btn-outline-light');
                btn.classList.add('btn-success', 'border-success');
            } else if (idx === selectedIndex && !isCorrect) {
                btn.classList.remove('btn-outline-light');
                btn.classList.add('btn-danger', 'border-danger');
            }
        });

        triviaResult.innerHTML = `
            <strong>${isCorrect ? 'Correct!' : 'Incorrect.'}</strong> <br>
            ${currentQuestion.expl}
        `;
        triviaResult.classList.remove('d-none');
    }

    if(nextBtn) nextBtn.addEventListener('click', loadTrivia);
    
    // Initial Load
    if(triviaQuestion) loadTrivia();


    // --- Glossary Logic ---
    const glossaryContainer = document.getElementById('glossary-container');
    const searchInput = document.getElementById('glossary-search');
    let allTerms = [];

    async function loadGlossary() {
        try {
            const res = await fetch('/api/learn/glossary');
            allTerms = await res.json();
            renderGlossary(allTerms);
        } catch (e) {
            glossaryContainer.innerHTML = '<div class="text-center text-danger">Failed to load glossary.</div>';
        }
    }

    function renderGlossary(terms) {
        glossaryContainer.innerHTML = '';
        if(terms.length === 0) {
            glossaryContainer.innerHTML = '<div class="text-center text-muted">No terms found.</div>';
            return;
        }

        terms.forEach(t => {
            const col = document.createElement('div');
            col.className = 'col-md-6';
            col.innerHTML = `
                <div class="p-3 border rounded-3 h-100 bg-white hover-lift">
                    <h5 class="fw-bold text-primary mb-1">${t.term}</h5>
                    <p class="small text-muted mb-0">${t.definition}</p>
                </div>
            `;
            glossaryContainer.appendChild(col);
        });
    }

    if(searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const filtered = allTerms.filter(t => 
                t.term.toLowerCase().includes(query) || 
                (t.definition && t.definition.toLowerCase().includes(query))
            );
            renderGlossary(filtered);
        });
    }

    if(glossaryContainer) loadGlossary();

});
