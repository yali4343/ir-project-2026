from Backend.data_Loader import load_index, load_pagerank, load_pageviews, load_id_to_title
from Backend.ranking import calculate_tfidf_score_with_dir, calculate_unique_term_count
from Backend.tokenizer import tokenize
import math

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
        Improved with weights and PageRank interaction.
        """
        tokens = tokenize(query)
        if hasattr(self, '_expand_query'):
            # Placeholder for query expansion if we implement it
            pass

        scores = {}
        
        # 1. Weights & Config
        w_text = 0.3
        w_title = 0.4
        w_anchor = 0.3
        w_pr = 0.5 
        
        # 2. Results from indices
        text_res = calculate_tfidf_score_with_dir(tokens, self.text_index, 'postings_gcp')
        title_res = calculate_tfidf_score_with_dir(tokens, self.title_index, 'postings_title')
        anchor_res = calculate_tfidf_score_with_dir(tokens, self.anchor_index, 'postings_anchor')
        
        # Helper to normalize
        def normalize(results):
            if not results: return {}
            max_score = max(score for _, score in results)
            if max_score == 0: return {doc_id: 0 for doc_id, _ in results}
            return {doc_id: score / max_score for doc_id, score in results}

        norm_text = normalize(text_res)
        norm_title = normalize(title_res)
        norm_anchor = normalize(anchor_res)
        
        # Union of all doc_ids
        all_ids = set(norm_text.keys()) | set(norm_title.keys()) | set(norm_anchor.keys())

        # --- Index Elimination (Chapter 7.1.2) ---
        # Refine candidates by requiring minimum term overlap in Body
        if len(tokens) > 1:
            term_counts = calculate_unique_term_count(tokens, self.text_index, 'postings_gcp')
            count_dict = dict(term_counts)
            
            # Threshold: 50% of query terms
            min_match = math.ceil(len(tokens) * 0.5)
            
            filtered_ids = set()
            for doc_id, count in count_dict.items():
                if count >= min_match:
                    filtered_ids.add(doc_id)
            
            # Intersect with existing candidates
            # Note: doc_ids in text_res are int/str? 
            # In calculate_unique_term_count, it returns what reads from index (int).
            # normalize keys are same.
            
            if filtered_ids:
               # Only apply filter if we haven't eliminated everything
               # (Safety fallback)
               all_ids = all_ids.intersection(filtered_ids)
             
        # Debugging: Print stats for first query call
        if not hasattr(self, '_debug_printed'):
            print(f"DEBUG: Query='{query}' Tokens={tokens} Candidates={len(all_ids)}")
            if all_ids:
                sample_id = list(all_ids)[0]
                print(f"Sample Doc {sample_id} -> Text:{norm_text.get(sample_id,0):.3f} Title:{norm_title.get(sample_id,0):.3f} Anchor:{norm_anchor.get(sample_id,0):.3f}")
            self._debug_printed = True

        # 4. Integrate PageRank
        for doc_id in all_ids:
            score = 0
            score += norm_text.get(doc_id, 0) * w_text
            score += norm_title.get(doc_id, 0) * w_title
            score += norm_anchor.get(doc_id, 0) * w_anchor
            
            pr_val = self.pagerank.get(doc_id, 0)
            try:
                # Log scale PR
                score += w_pr * math.log(pr_val + 1)
            except:
                pass
            
            scores[doc_id] = score

        # Format results
        final_res = []
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
        # Requirement: Descending order of DISTINCT query words.
        # This sounds like the search_anchor/search_title special requirement.
        # The prompt only specified it explicitly for ANCHOR ("search_anchor behavior").
        # For Title, Chapter 7 mentions "Inexact Top K".
        # However, checking the Forum Clarifications block in prompt:
        # "search_anchor must ... Rank documents by the number of UNIQUE query words"
        # It doesn't explicitly force this for search_title, BUT existing search_title docstring says:
        # "ordered in descending order of the NUMBER OF DISTINCT QUERY WORDS"
        # So I should use the same logic for Title as well!
        res = calculate_unique_term_count(tokens, self.title_index, 'postings_title')
        return self._format(res)

    def search_anchor(self, query):
        tokens = tokenize(query)
        # Requirement: Rank by number of UNIQUE query words.
        res = calculate_unique_term_count(tokens, self.anchor_index, 'postings_anchor')
        return self._format(res)
        
    def _format(self, results):
        final_res = []
        for doc_id, score in sorted(results, key=lambda x: x[1], reverse=True)[:100]:
            # Ensure doc_id is properly looked up (int vs str)
            # Data loader returns int keys usually?
            # pickle index stores int.
            # id_to_title keys?
            # Let's try int then str.
            try:
                did_int = int(doc_id)
                title = self.id_to_title.get(did_int, str(doc_id))
            except:
                title = self.id_to_title.get(doc_id, str(doc_id))
                
            final_res.append((str(doc_id), title))
        return final_res
        
    def get_pagerank(self, wiki_ids):
        return [self.pagerank.get(doc_id, 0) for doc_id in wiki_ids]

    def get_pageviews(self, wiki_ids):
        return [self.pageviews.get(doc_id, 0) for doc_id in wiki_ids]
