from Backend.data_Loader import load_index, load_pagerank, load_pageviews, load_id_to_title
from Backend.ranking import calculate_tfidf_score_with_dir
from Backend.tokenizer import tokenize

class SearchEngine:
    def __init__(self):
        print("Initializing Search Engine...")
        self.text_index = load_index('text')
        self.title_index = load_index('title')
        self.anchor_index = load_index('anchor')
        self.pagerank = load_pagerank()
        self.pageviews = load_pageviews()
        self.id_to_title = load_id_to_title()
        print("Search Engine initialized.")
        
    def search(self, query):
        """
        Combined search using all indices.
        """
        tokens = tokenize(query)
        scores = {}
        
        # Text Search (Using postings_gcp folder)
        text_res = calculate_tfidf_score_with_dir(tokens, self.text_index, 'postings_gcp')
        for doc_id, score in text_res:
            scores[doc_id] = scores.get(doc_id, 0) + score * 1.0 # Weight for body
            
        # Title Search (Using postings_title folder)
        title_res = calculate_tfidf_score_with_dir(tokens, self.title_index, 'postings_title')
        for doc_id, score in title_res:
            scores[doc_id] = scores.get(doc_id, 0) + score * 1.0 # Weight for title
            
        # Anchor Search (Using postings_anchor folder)
        anchor_res = calculate_tfidf_score_with_dir(tokens, self.anchor_index, 'postings_anchor')
        for doc_id, score in anchor_res:
            scores[doc_id] = scores.get(doc_id, 0) + score * 1.0 # Weight for anchor
            
        # Format results
        final_res = []
        # Sort by score descending
        for doc_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:100]:
            title = self.id_to_title.get(doc_id, str(doc_id))
            final_res.append((str(doc_id), title))
            
        return final_res
        
    def search_body(self, query):
        tokens = tokenize(query)
        res = calculate_tfidf_score_with_dir(tokens, self.text_index, 'postings_gcp')
        return self._format(res)
        
    def search_title(self, query):
        tokens = tokenize(query)
        res = calculate_tfidf_score_with_dir(tokens, self.title_index, 'postings_title')
        return self._format(res)

    def search_anchor(self, query):
        tokens = tokenize(query)
        res = calculate_tfidf_score_with_dir(tokens, self.anchor_index, 'postings_anchor')
        return self._format(res)
        
    def _format(self, results):
        final_res = []
        for doc_id, score in sorted(results, key=lambda x: x[1], reverse=True)[:100]:
            title = self.id_to_title.get(doc_id, str(doc_id))
            final_res.append((str(doc_id), title))
        return final_res
        
    def get_pagerank(self, wiki_ids):
        return [self.pagerank.get(doc_id, 0) for doc_id in wiki_ids]

    def get_pageviews(self, wiki_ids):
        return [self.pageviews.get(doc_id, 0) for doc_id in wiki_ids]
