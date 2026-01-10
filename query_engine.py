from Backend.data_Loader import (
    load_index,
    load_pagerank,
    load_pageviews,
    load_id_to_title,
)
from Backend.ranking import calculate_tfidf_score_with_dir, calculate_unique_term_count
from Backend.tokenizer import tokenize
import math


class SearchEngine:
    """
    Main search engine class that coordinates loading indices and executing search queries.
    Integration point for different ranking methods, PageRank, and data loading.

    Attributes:
        text_index (InvertedIndex): The inverted index for the text body.
        pagerank (dict): PageRank scores for documents.
        pageviews (dict): Page view counts for documents.
        id_to_title (dict): Mapping from document IDs to titles.
    """

    def __init__(self):
        """
        Initializes the Search Engine by loading necessary data structures.
        Loads inverted index (text), PageRank scores, page views, and title mappings.
        """
        print("Initializing Search Engine")
        self.text_index = load_index("text")
        # self.title_index = load_index('title') # Removed
        # self.anchor_index = load_index('anchor') # Removed
        self.pagerank = load_pagerank()
        self.pageviews = load_pageviews()
        self.id_to_title = load_id_to_title()
        print("Search Engine initialized.")

    def search(self, query):
        """
        Executes a combined search using only Body index and PageRank.

        Orchestrates the retrieval process:
        1. Tokens generation.
        2. TF-IDF calculation on Body.
        3. Index elimination elimination based on query term overlap.
        4. Integration of PageRank scores.

        Args:
            query (str): The search query string.

        Returns:
            list: A list of tuples (doc_id, title) for the top ranked documents.
                  Returns up to 100 results.
        """
        tokens = tokenize(query)
        scores = {}

        # 1. Weights & Config
        w_text = 0.85
        w_pr = 0.15

        # 2. Results from indices (Only Text)
        text_res = calculate_tfidf_score_with_dir(
            tokens, self.text_index, "postings_gcp"
        )

        # Helper to normalize
        def normalize(results):
            if not results:
                return {}
            max_score = max(score for _, score in results)
            if max_score == 0:
                return {doc_id: 0 for doc_id, _ in results}
            return {doc_id: score / max_score for doc_id, score in results}

        norm_text = normalize(text_res)

        # Union of all doc_ids (Only Text)
        all_ids = set(norm_text.keys())

        # --- Index Elimination (Chapter 7.1.2) ---
        # Refine candidates by requiring minimum term overlap in Body
        if len(tokens) > 1:
            term_counts = calculate_unique_term_count(
                tokens, self.text_index, "postings_gcp"
            )
            count_dict = dict(term_counts)

            # Threshold: 50% of query terms
            min_match = math.ceil(len(tokens) * 0.5)

            filtered_ids = set()
            for doc_id, count in count_dict.items():
                if count >= min_match:
                    filtered_ids.add(doc_id)

            if filtered_ids:
                all_ids = all_ids.intersection(filtered_ids)

        # 4. Integrate PageRank
        # Pre-calculated Min/Max Log(PR+1) from data analysis
        min_log_pr = 0.14
        max_log_pr = 9.2

        for doc_id in all_ids:
            text_score = norm_text.get(doc_id, 0)

            pr_val = self.pagerank.get(doc_id, 0)
            # Normalize PR to [0, 1] range
            log_pr = math.log(pr_val + 1)
            norm_pr = (log_pr - min_log_pr) / (max_log_pr - min_log_pr)
            # Clamp to [0,1] just in case
            norm_pr = max(0.0, min(1.0, norm_pr))

            # Combined score
            scores[doc_id] = (w_text * text_score) + (w_pr * norm_pr)

        # Format results
        final_res = []
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[
            :100
        ]:
            title = None
            try:
                title = self.id_to_title.get(int(doc_id))
            except:
                pass
            if title is None:
                title = self.id_to_title.get(doc_id, str(doc_id))
            final_res.append((str(doc_id), title))

        return final_res

    def search_body(self, query):
        """
        Searches using only the body text index.
        Useful for debugging or specific text-only queries.

        Args:
            query (str): The search query string.

        Returns:
            list: A list of tuples (doc_id, title) for the top ranked documents.
        """
        tokens = tokenize(query)
        res = calculate_tfidf_score_with_dir(tokens, self.text_index, "postings_gcp")
        return self._format(res)

    def search_title(self, query):
        """
        Placeholder for title search. Currently returns empty list.

        Args:
            query (str): The search query string.

        Returns:
            list: Empty list.
        """
        return []

    def search_anchor(self, query):
        """
        Placeholder for anchor text search. Currently returns empty list.

        Args:
            query (str): The search query string.

        Returns:
            list: Empty list.
        """
        return []

    def _format(self, results):
        """
        Formats the raw search results into the expected output structure.
        Resolves document IDs to titles.

        Args:
            results (list): A list of tuples (doc_id, score).

        Returns:
            list: A list of tuples (doc_id, title) sorted by score.
        """
        final_res = []
        for doc_id, score in sorted(results, key=lambda x: x[1], reverse=True)[:100]:
            title = None
            try:
                title = self.id_to_title.get(int(doc_id))
            except:
                pass
            if title is None:
                title = self.id_to_title.get(doc_id, str(doc_id))
            final_res.append((str(doc_id), title))
        return final_res

    def get_pagerank(self, wiki_ids):
        """
        Retrieves PageRank scores for a list of document IDs.

        Args:
            wiki_ids (list): List of document IDs.

        Returns:
            list: List of PageRank scores corresponding to the input IDs.
        """
        return [self.pagerank.get(doc_id, 0) for doc_id in wiki_ids]

    def get_pageviews(self, wiki_ids):
        """
        Retrieves page view counts for a list of document IDs.

        Args:
            wiki_ids (list): List of document IDs.

        Returns:
            list: List of page view counts corresponding to the input IDs.
        """
        return [self.pageviews.get(doc_id, 0) for doc_id in wiki_ids]
