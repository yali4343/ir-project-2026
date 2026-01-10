from Backend.data_Loader import (
    load_index,
    load_pagerank,
    load_pageviews,
    load_id_to_title,
)
from Backend.ranking_v2 import (
    get_candidate_documents,
    calculate_unique_term_count,
    calculate_tfidf_score_with_dir,
)
from Backend.tokenizer import tokenize
from Backend.semantic_expansion import SemanticExpander
import math
import heapq


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

        # Initialize Semantic Expander
        self.expander = SemanticExpander(model_path="data/word2vec.model")

        # Compute AvgDL for BM25 if DL is available
        self.avgdl = 0
        if hasattr(self.text_index, "DL"):
            self.avgdl = sum(self.text_index.DL.values()) / len(self.text_index.DL)
            # Monkey patch the index to have avgdl property if we want consistency
            self.text_index.avgdl = self.avgdl

        print("Search Engine initialized.")

    def search(self, query):
        """
        Executes a combined search using only Body index and PageRank.
        Uses efficient 2-stage retrieval:
        1. BM25 scoring with candidate limiting (Heap)
        2. Re-ranking top candidates with PageRank

        Args:
            query (str): The search query string.

        Returns:
            list: A list of tuples (doc_id, title) for the top ranked documents.
                  Returns up to 100 results.
        """
        tokens = tokenize(query)
        if not tokens:
            return []

        token_weights = {t: 1.0 for t in tokens}

        # --- Query Expansion (Weak Queries) ---
        # Heuristic: Short queries or low unique terms
        if len(tokens) <= 2:
            expanded = self.expander.expand(tokens)
            for t in expanded:
                if t not in token_weights:
                    token_weights[t] = 0.3  # Constraint: weight <= 0.3
                    tokens.append(t)

        # --- Index Elimination / Pruning ---
        # Sort tokens by IDF (assuming high IDF > low IDF)
        # N = len(self.text_index.posting_locs)
        # idfs = [(t, math.log(N/self.text_index.df[t], 10)) for t in set(tokens) if t in self.text_index.df]
        # idfs.sort(key=lambda x: x[1], reverse=True)
        #
        # For broad queries ("United States" -> both low IDF), we might keep both.
        # But if we have many tokens, keep top M.
        # Implementation: If > 4 tokens, keep top 75%. If <= 4, keep all (unless stopword-ish).
        # Since we tokenized stopwords out, we assume remaining are useful.

        pruned_tokens = tokens

        # --- Stage 1: Candidate Limiting (BM25) ---
        # Get top 2000 docs roughly
        N_CANDIDATES = 2000
        candidates_list = get_candidate_documents(
            pruned_tokens,
            self.text_index,
            "postings_gcp",
            k=N_CANDIDATES,
            token_weights=token_weights,
        )

        if not candidates_list:
            return []

        # --- Stage 2: PageRank Integration ---
        # Normalize BM25 scores
        max_score = candidates_list[0][
            1
        ]  # Sorted/Heap returns descend? heapq.nlargest returns desc.
        if max_score <= 0:
            max_score = 1

        w_text = 0.85
        w_pr = 0.15

        # Pre-calculated Min/Max Log(PR+1)
        min_log_pr = 0.14
        max_log_pr = 9.2  # From given context

        final_scores = []

        for doc_id, bm25_score in candidates_list:
            norm_bm25 = bm25_score / max_score

            pr_val = self.pagerank.get(doc_id, 0)
            log_pr = math.log(pr_val + 1)
            norm_pr = (log_pr - min_log_pr) / (max_log_pr - min_log_pr)
            norm_pr = max(0.0, min(1.0, norm_pr))

            final_score = (w_text * norm_bm25) + (w_pr * norm_pr)
            final_scores.append((str(doc_id), final_score))

        # Sort top 100
        # final_scores is typically small (2000 items), sorted is fast.
        top_100 = sorted(final_scores, key=lambda x: x[1], reverse=True)[:100]

        # Format (Fetch titles ONLY for top 100)
        res = []
        for doc_id, score in top_100:
            title = None
            try:
                title = self.id_to_title.get(int(doc_id))
            except:
                pass
            if title is None:
                title = self.id_to_title.get(doc_id, str(doc_id))
            res.append((doc_id, title))

        return res

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
        # Use existing legacy/debug function, but formats it
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
        # Sort if not sorted? results might be from legacy dict items
        sorted_res = sorted(results, key=lambda x: x[1], reverse=True)[:100]

        for doc_id, score in sorted_res:
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
