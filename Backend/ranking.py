import math
import os
from collections import Counter
import sys

# Add project root to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def calculate_tfidf_score(query_tokens, index):
    """
    Calculates TF-IDF cosine similarity for the query against the index.
    Returns a dictionary {doc_id: score}.
    """
    # 1. Calculate Query TF-IDF
    query_counter = Counter(query_tokens)
    query_norm = 0
    query_weights = {}
    
    for token, count in query_counter.items():
        if token in index.df:
            tf = count / len(query_tokens) # Term frequency in query
            # Handle missing DL (Total number of documents)
            N = len(index.posting_locs) if not hasattr(index, 'DL') else len(index.DL)
            idf = math.log(N / index.df[token], 10) # IDF
            w_iq = tf * idf
            query_weights[token] = w_iq
            query_norm += w_iq ** 2
    
    query_norm = math.sqrt(query_norm)
    if query_norm == 0:
        return []

    # 2. Calculate Scores
    scores = Counter()
    
    # Logic to determine where to read posting lists from
    # We assume 'postings_gcp' is the folder name in the bucket or local dir
    # Note: Even though we split indexes to text/title/anchor pkl files, 
    # the BIN files are likely still in 'postings_gcp' folder (or respective folders)
    # The user instruction didn't mention moving bin files, so we assume they are 
    # where the original code expected them, or in the bucket.
    
    # We'll use a heuristic: if we are using 'text_index', maybe look in 'postings_gcp'?
    # Or just default to 'postings_gcp' as per original code.
    # The original code hardcoded 'postings_gcp' for body, 'postings_title' for title.
    # We need to know WHICH index we are querying to pick the folder.
    # BUT calculate_tfidf_score takes 'index' object, it doesn't know the folder name.
    # We might need to pass the folder name.
    
    # Let's inspect the call site in original code:
    # index_body -> 'postings_gcp'
    # index_title -> 'postings_title'
    # index_anchor -> 'postings_anchor'
    
    # We should update the signature to accept 'posting_list_dir'.
    # But since we are adapting, let's try to pass it.
    
    # Update: I will change the signature to accept 'posting_list_dir'.
    pass

def calculate_tfidf_score_with_dir(query_tokens, index, posting_list_dir):
    """
    Calculates TF-IDF cosine similarity for the query against the index.
    Returns a list of (doc_id, score).
    """
    # 1. Calculate Query TF-IDF
    query_counter = Counter(query_tokens)
    query_norm = 0
    query_weights = {}
    
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

    # 2. Calculate Scores
    scores = Counter()
    
    # Determine local vs bucket
    base_dir = posting_list_dir
    bucket_name = Config.BUCKET_NAME
    
    # Check if local exists
    local_path = os.path.join('data', base_dir)
    if os.path.exists(local_path) and os.path.isdir(local_path):
        # Check if bin files exist
        has_bin = any(f.endswith('.bin') for f in os.listdir(local_path))
        if has_bin:
            base_dir = local_path
            bucket_name = None # Use local
    
    # If bucket_name is NOT None, base_dir should be just the folder name (e.g. 'postings_gcp')
    
    for token, w_iq in query_weights.items():
        try:
            posting_list = index.read_a_posting_list(base_dir, token, bucket_name)
        except Exception as e:
            # print(f"Error reading posting list for {token}: {e}")
            continue
        
        for doc_id, tf in posting_list:
            idf = math.log(N / index.df[token], 10)
            w_ij = tf * idf 
            scores[doc_id] += w_iq * w_ij

    # 3. Normalize
    final_scores = []
    for doc_id, score in scores.items():
        norm_score = score / query_norm
        final_scores.append((doc_id, norm_score))
        
    return final_scores
