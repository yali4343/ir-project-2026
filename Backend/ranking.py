import math
import os
from collections import Counter
import sys

# Add project root to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def _get_posting_source(posting_list_dir):
    """
    Helper to determine if we should read from local 'data/' or bucket.
    """
    base_dir = posting_list_dir
    bucket_name = Config.BUCKET_NAME
    index_source = os.environ.get('INDEX_SOURCE', 'auto')

    # Force GCS if configured
    if index_source == 'gcs':
        return base_dir, bucket_name

    # Otherwise check local
    local_path = os.path.join('data', base_dir)
    if index_source != 'gcs':
        if os.path.exists(local_path) and os.path.isdir(local_path):
            has_bin = any(f.endswith('.bin') for f in os.listdir(local_path))
            if has_bin:
                return local_path, None
    
    return base_dir, bucket_name

def calculate_tfidf_score_with_dir(query_tokens, index, posting_list_dir):
    """
    Calculates TF-IDF cosine similarity for the query against the index.
    Returns a list of (doc_id, score).
    """
    query_counter = Counter(query_tokens)
    query_norm = 0
    query_weights = {}
    
    # N = number of docs. Use posting_locs length as proxy if DL not available
    N = len(index.posting_locs) if not hasattr(index, 'DL') else len(index.DL)
    
    for token, count in query_counter.items():
        if token in index.df:
            tf = count / len(query_tokens) 
            idf = math.log(N / index.df[token], 10) 
            w_iq = tf * idf
            query_weights[token] = w_iq
            query_norm += w_iq ** 2
    
    query_norm = math.sqrt(query_norm)
    if query_norm == 0:
        return []

    scores = Counter()
    base_dir, bucket_name = _get_posting_source(posting_list_dir)
    
    for token, w_iq in query_weights.items():
        try:
            posting_list = index.read_a_posting_list(base_dir, token, bucket_name)
        except Exception:
            continue
        
        for doc_id, tf in posting_list:
            idf = math.log(N / index.df[token], 10)
            w_ij = tf * idf 
            scores[doc_id] += w_iq * w_ij

    final_scores = []
    for doc_id, score in scores.items():
        norm_score = score / query_norm
        final_scores.append((doc_id, norm_score))
        
    return final_scores

def calculate_unique_term_count(query_tokens, index, posting_list_dir):
    """
    Calculates score based on Number of UNIQUE query words in the document.
    """
    unique_tokens = set(query_tokens)
    scores = Counter()
    
    base_dir, bucket_name = _get_posting_source(posting_list_dir)
    
    for token in unique_tokens:
        try:
            posting_list = index.read_a_posting_list(base_dir, token, bucket_name)
        except Exception:
            continue
            
        for doc_id, _ in posting_list:
            scores[doc_id] += 1
            
    # Rank by count (descending), break ties with Doc ID (or anything, really)
    # The requirement is descending order of unique query words.
    results = []
    for doc_id, count in scores.items():
        results.append((doc_id, count))
        
    return results
