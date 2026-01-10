/**
 * Frontend logic for the Search Engine UI.
 * Handles DOM manipulation, event listeners, and data fetching from the backend API.
 *
 * Key DOM elements:
 * - #search-btn: Button to trigger search.
 * - #query: Input field for search text.
 * - #results-list: Container (ul) for displaying results.
 * - #loading: Loading indicator.
 */

document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("search-btn");
  const queryInput = document.getElementById("query");
  const resultsList = document.getElementById("results-list");
  const loading = document.getElementById("loading");

  /**
   * Executes the search operation.
   * 1. Reads query from input.
   * 2. Shows loading state.
   * 3. Fetches results from /search API.
   * 4. Renders results as list items.
   *
   * @async
   * @returns {Promise<void>}
   */
  const performSearch = async () => {
    const query = queryInput.value.trim();
    if (!query) return;

    resultsList.innerHTML = "";
    loading.classList.remove("hidden");

    try {
      // API Call
      // Endpoint: /search
      // Param: query (string)
      const response = await fetch(
        `/search?query=${encodeURIComponent(query)}`
      );
      const data = await response.json();

      loading.classList.add("hidden");

      if (data.length === 0) {
        resultsList.innerHTML = '<li class="no-results">No results found.</li>';
        return;
      }

      // Render Results
      // Expected data format: Array<[doc_id, title]>
      data.forEach(([id, title]) => {
        const li = document.createElement("li");
        li.className = "result-item";

        // Wiki ID -> https://en.wikipedia.org/?curid=ID
        const link = `https://en.wikipedia.org/?curid=${id}`;

        li.innerHTML = `
                    <a href="${link}" class="result-title" target="_blank">${title}</a>
                    <div class="result-meta">ID: ${id}</div>
                `;
        resultsList.appendChild(li);
      });
    } catch (error) {
      console.error("Error:", error);
      loading.classList.add("hidden");
      resultsList.innerHTML =
        '<li class="error">An error occurred. Please try again.</li>';
    }
  };

  searchBtn.addEventListener("click", performSearch);
  queryInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") performSearch();
  });
});
