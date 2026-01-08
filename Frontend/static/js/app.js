document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('search-btn');
    const queryInput = document.getElementById('query');
    const resultsList = document.getElementById('results-list');
    const loading = document.getElementById('loading');

    const performSearch = async () => {
        const query = queryInput.value.trim();
        if (!query) return;

        resultsList.innerHTML = '';
        loading.classList.remove('hidden');

        try {
            const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            loading.classList.add('hidden');
            
            if (data.length === 0) {
                resultsList.innerHTML = '<li class="no-results">No results found.</li>';
                return;
            }

            // data is [[id, title], [id, title], ...]
            data.forEach(([id, title]) => {
                const li = document.createElement('li');
                li.className = 'result-item';
                
                // Wiki ID -> https://en.wikipedia.org/?curid=ID
                const link = `https://en.wikipedia.org/?curid=${id}`;
                
                li.innerHTML = `
                    <a href="${link}" class="result-title" target="_blank">${title}</a>
                    <div class="result-meta">ID: ${id}</div>
                `;
                resultsList.appendChild(li);
            });
        } catch (error) {
            console.error('Error:', error);
            loading.classList.add('hidden');
            resultsList.innerHTML = '<li class="error">An error occurred. Please try again.</li>';
        }
    };

    searchBtn.addEventListener('click', performSearch);
    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
});
