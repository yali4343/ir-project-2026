import math
import os
from collections import Counter
import sys
import heapq

# Add project root to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


def _get_posting_source(posting_list_dir):
    """
    Helper to determine if we should read posting lists from local 'data/' or GCS bucket.
    """
    base_dir = posting_list_dir
    bucket_name = Config.BUCKET_NAME
    index_source = os.environ.get("INDEX_SOURCE", "auto")

    # Force GCS if configured
    if index_source == "gcs":
        return base_dir, bucket_name

    # Otherwise check local
    local_path = os.path.join("data", base_dir)
    if index_source != "gcs":
        if os.path.exists(local_path) and os.path.isdir(local_path):
            has_bin = any(f.endswith(".bin") for f in os.listdir(local_path))
            if has_bin:
                return local_path, None

    return base_dir, bucket_name


def calculate_tfidf_score_with_dir(query_tokens, index, posting_list_dir):
    """
    Legacy/Debug TF-IDF function.
    Calculates TF-IDF cosine similarity for the query against the index.
    """
    query_counter = Counter(query_tokens)
    query_norm = 0
    query_weights = {}

    N = len(index.posting_locs) if not hasattr(index, "DL") else len(index.DL)

    for token, count in query_counter.items():
        if token in index.df:
            tf = count / len(query_tokens)
            idf = math.log(N / index.df[token], 10)
            w_iq = tf * idf
            query_weights[token] = w_iq
            query_norm += w_iq**2

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
            # w_ij = tf * idf (TF-IDF standard)
            w_ij = tf * idf
            scores[doc_id] += w_iq * w_ij

    final_scores = []
    for doc_id, score in scores.items():
        norm_score = score / query_norm
        final_scores.append((doc_id, norm_score))

    return final_scores


def get_candidate_documents(
    query_tokens, index, posting_list_dir, k=2000, token_weights=None
):
    """
    Stage 1: Efficiently Retrieve top-K candidates using BM25
    Uses heapq for top-K.
    """
    if not query_tokens:
        return []

    query_counter = Counter(query_tokens)

    # BM25 Parameters
    k1 = 1.2
    b = 0.75

    # Check for DL
    has_dl = hasattr(index, "DL")
    N = len(index.DL) if has_dl else len(index.posting_locs)

    avgdl = 0
    if has_dl:
        if hasattr(index, "avgdl"):
            avgdl = index.avgdl
        elif N > 0:
            avgdl = sum(index.DL.values()) / N

    # If stats missing, fallback to b=0 (BM25 -> TF-IDF like behavior for length)
    if not has_dl or avgdl == 0:
        b = 0

    scores = Counter()
    base_dir, bucket_name = _get_posting_source(posting_list_dir)

    for token in query_counter:
        if token not in index.df:
            continue

        try:
            posting_list = index.read_a_posting_list(base_dir, token, bucket_name)
        except:
            continue

        # IDF
        df = index.df[token]
        # Robust log
        try:
            # BM25 IDF
            idf = math.log(((N - df + 0.5) / (df + 0.5)) + 1)
        except:
            idf = 0

        q_count = query_counter[token]
        # Apply custom weight if provided (e.g. for expansion)
        weight = 1.0
        if token_weights and token in token_weights:
            weight = token_weights[token]

        # Query saturation could be: ((k3 + 1)*q_count) / (k3 + q_count)
        # But we simply multiply the final score by the weight/importance of the term

        for doc_id, tf in posting_list:
            # BM25 score for this term
            if b == 0:
                denom = tf + k1
            else:
                doc_len = index.DL.get(doc_id, avgdl)
                denom = tf + k1 * (1 - b + b * doc_len / avgdl)

            num = idf * tf * (k1 + 1)
            term_score = num / denom

            scores[doc_id] += term_score * weight

    # Efficient Top-K
    return heapq.nlargest(k, scores.items(), key=lambda x: x[1])


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

    # Rank by count (descending)
    results = []
    for doc_id, count in scores.items():
        results.append((doc_id, count))

    return sorted(results, key=lambda x: x[1], reverse=True)
