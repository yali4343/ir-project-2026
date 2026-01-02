from flask import Flask, request, jsonify
import sys
import os
import math
from collections import Counter
import re
import pickle

# Add the src directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from inverted_index_gcp import InvertedIndex, MultiFileReader
from config import Config

class MyFlaskApp(Flask):
    def run(self, host=None, port=None, debug=None, **options):
        super(MyFlaskApp, self).run(host=host, port=port, debug=debug, **options)

app = MyFlaskApp(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# --- Global Variables ---
index_body = None
index_title = None
index_anchor = None
page_rank = {}
page_views = {}
id_to_title = {}

def load_index():
    global index_body, index_title, index_anchor, page_rank, page_views, id_to_title
    print("Loading inverted indexes...")
    
    # 1. Load Body Index
    try:
        # Try loading from local 'data' folder first (fastest for dev)
        index_body = InvertedIndex.read_index('data/postings_gcp', 'index')
        print("Loaded body index from local data.")
    except Exception as e:
        print(f"Could not load local body index: {e}")
        try:
            # Fallback to bucket
            index_body = InvertedIndex.read_index('postings_gcp', 'index', Config.BUCKET_NAME)
            print("Loaded body index from bucket.")
        except Exception as e2:
            print(f"Could not load body index from bucket: {e2}")
            index_body = InvertedIndex()

    # 2. Load Title Index
    try:
        index_title = InvertedIndex.read_index('data/postings_title', 'index')
        print("Loaded title index from local data.")
    except:
        try:
            index_title = InvertedIndex.read_index('postings_title', 'index', Config.BUCKET_NAME)
            print("Loaded title index from bucket.")
        except:
            print("Could not load title index.")
            index_title = InvertedIndex()

    # 3. Load Anchor Index
    try:
        index_anchor = InvertedIndex.read_index('data/postings_anchor', 'index')
        print("Loaded anchor index from local data.")
    except:
        try:
            index_anchor = InvertedIndex.read_index('postings_anchor', 'index', Config.BUCKET_NAME)
            print("Loaded anchor index from bucket.")
        except:
            print("Could not load anchor index.")
            index_anchor = InvertedIndex()

    # 4. Load ID to Title Mapping
    try:
        # Try local first
        if os.path.exists('data/id_to_title.pkl'):
            with open('data/id_to_title.pkl', 'rb') as f:
                id_to_title = pickle.load(f)
            print("Loaded id_to_title from local.")
        else:
            # Try bucket (assuming it's a blob named 'id_to_title.pkl')
            # We need to implement reading pickle from bucket if we want this
            # For now, let's assume we download it to data/
            pass
    except Exception as e:
        print(f"Could not load id_to_title: {e}")

    # 5. Load PageRank
    try:
        if os.path.exists('data/pagerank.pkl'):
            with open('data/pagerank.pkl', 'rb') as f:
                page_rank = pickle.load(f)
            print("Loaded pagerank from local.")
    except:
        pass

    # 6. Load PageViews
    try:
        if os.path.exists('data/pageviews.pkl'):
            with open('data/pageviews.pkl', 'rb') as f:
                page_views = pickle.load(f)
            print("Loaded pageviews from local.")
    except:
        pass

# Load index on startup
# In a real Flask app, this might be done differently, but for this simple server:
with app.app_context():
    load_index()

# --- Helper Functions ---
RE_WORD = re.compile(r"""[\#\@\w](['\-]?\w){2,24}""", re.UNICODE)
stopwords_frozen = frozenset(['corp', 're', 'is', 'has', 'mightn', 'd', 'll', 'y', 's', 't', 've', 'm', 'o', 'won', 'now', 'am', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in', 'me', 'my', 'no', 'of', 'on', 'or', 'so', 'to', 'up', 'us', 'we', 'ad', 'af', 'ah', 'ai', 'am', 'an', 'as', 'at', 'aw', 'ax', 'ay', 'ba', 'be', 'bi', 'bo', 'by', 'ch', 'do', 'dy', 'eh', 'el', 'em', 'en', 'er', 'es', 'et', 'ex', 'fa', 'go', 'ha', 'he', 'hi', 'hm', 'ho', 'id', 'if', 'in', 'is', 'it', 'jo', 'ka', 'ki', 'la', 'li', 'lo', 'ma', 'me', 'mi', 'mm', 'mo', 'mu', 'my', 'na', 'ne', 'no', 'nu', 'od', 'oe', 'of', 'oh', 'oi', 'ok', 'om', 'on', 'op', 'or', 'os', 'ow', 'ox', 'oy', 'pa', 'pe', 'pi', 'po', 'qi', 're', 'sh', 'si', 'so', 'ta', 'ti', 'to', 'uh', 'um', 'un', 'up', 'us', 'ut', 'we', 'wo', 'xi', 'xu', 'ya', 'ye', 'yo', 'za'])

def tokenize(text):
    """
    Basic tokenizer that removes stopwords and keeps words of length > 2.
    """
    list_of_tokens = [token.group() for token in RE_WORD.finditer(text.lower())]
    return [token for token in list_of_tokens if token not in stopwords_frozen]

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
    # score[d] = sum(w_iq * w_ij)
    # We need to traverse the posting lists of the query terms
    scores = Counter()
    
    # We need to read posting lists. 
    # If index is loaded from bucket, we need to pass the bucket name.
    # If local, bucket_name is None.
    # We assume 'postings_gcp' is the folder name in the bucket or local dir
    base_dir = 'postings_gcp' 
    bucket_name = Config.BUCKET_NAME if not os.path.exists(os.path.join('data', base_dir)) else None
    
    # If local, adjust base_dir to include 'data/'
    if bucket_name is None:
        base_dir = os.path.join('data', base_dir)

    for token, w_iq in query_weights.items():
        # Read posting list for this token
        # posting_list is a list of (doc_id, tf)
        try:
            posting_list = index.read_a_posting_list(base_dir, token, bucket_name)
        except Exception as e:
            print(f"Error reading posting list for {token}: {e}")
            continue
        
        for doc_id, tf in posting_list:
            # Calculate w_ij (TF-IDF for document)
            # We need doc_len for TF normalization? 
            # Usually TF in document is just 'tf' or 'tf/doc_len'.
            # If we don't have doc_len, we can use raw TF or log(1+tf).
            # Let's use standard tf-idf: (tf / doc_len) * idf
            # BUT we don't have doc_len loaded efficiently for all docs yet.
            # Assumption: For now, let's use raw TF * IDF or just TF.
            # The instructions say "cosine similarity using tf-idf".
            # If we lack DL, we can't normalize by doc length.
            # Let's assume raw TF for now and refine later if we get DL.
            
            # w_ij = (tf) * idf  <-- Simplified without doc length normalization
            # N is already calculated above
            idf = math.log(N / index.df[token], 10)
            w_ij = tf * idf 
            
            scores[doc_id] += w_iq * w_ij

    # 3. Normalize by Document Length (Cosine Similarity)
    # Cosine(q, d) = DotProduct(q, d) / (|q| * |d|)
    # We have DotProduct in 'scores'. We have |q| in 'query_norm'.
    # We need |d|. 
    # If we don't have |d|, we return the DotProduct (unnormalized cosine).
    # Or we can try to approximate or load DL if available.
    
    final_scores = []
    for doc_id, score in scores.items():
        # norm_score = score / (query_norm * index.DL.get(doc_id, 1))
        # For now, unnormalized or just query normalized
        norm_score = score / query_norm
        final_scores.append((doc_id, norm_score))
        
    return final_scores

@app.route("/search")
def search():
    ''' Returns up to a 100 of your best search results for the query. This is 
        the place to put forward your best search engine, and you are free to
        implement the retrieval whoever you'd like within the bound of the 
        project requirements (efficiency, quality, etc.). That means it is up to
        you to decide on whether to use stemming, remove stopwords, use 
        PageRank, query expansion, etc.

        To issue a query navigate to a URL like:
         http://YOUR_SERVER_DOMAIN/search?query=hello+world
        where YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of up to 100 search results, ordered from best to worst where each 
        element is a tuple (wiki_id, title).
    '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    # BEGIN SOLUTION

    # END SOLUTION
    return jsonify(res)

@app.route("/search_body")
def search_body():
    ''' Returns up to a 100 search results for the query using TFIDF AND COSINE
        SIMILARITY OF THE BODY OF ARTICLES ONLY. DO NOT use stemming. DO USE the 
        staff-provided tokenizer from Assignment 3 (GCP part) to do the 
        tokenization and remove stopwords. 

        To issue a query navigate to a URL like:
         http://YOUR_SERVER_DOMAIN/search_body?query=hello+world
        where YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of up to 100 search results, ordered from best to worst where each 
        element is a tuple (wiki_id, title).
    '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    
    # BEGIN SOLUTION
    query_tokens = tokenize(query)
    
    # Check if index is loaded
    if index_body is None:
        print("Index not loaded!")
        return jsonify([])

    # We need a way to get document titles. 
    # Usually, there's an id_map or titles index.
    # For now, we'll return doc_id as title if we don't have the map.
    
    # Calculate scores
    # Note: calculate_tfidf_score needs 'index.DL' which we might not have.
    # We need to patch InvertedIndex to have a dummy DL or load it.
    
    # Temporary fix for DL if missing in index object
    if not hasattr(index_body, 'DL'):
        # Use a large number or estimate if not available
        # Or just use the number of docs in the index as N
        # N = len(index_body.posting_locs) # Approximation
        # index_body.DL = {doc_id: 1 for doc_id in ...} # Dummy
        pass

    scores = calculate_tfidf_score(query_tokens, index_body)
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Take top 100
    top_100 = scores[:100]
    
    # Map to (wiki_id, title)
    # We need a title mapping. 
    # If we don't have it, we return (wiki_id, str(wiki_id))
    res = [(str(doc_id), id_to_title.get(str(doc_id), str(doc_id))) for doc_id, score in top_100]
    
    # END SOLUTION
    return jsonify(res)

@app.route("/search_title")
def search_title():
    ''' Returns ALL (not just top 100) search results that contain A QUERY WORD 
        IN THE TITLE of articles, ordered in descending order of the NUMBER OF 
        DISTINCT QUERY WORDS that appear in the title. DO NOT use stemming. DO 
        USE the staff-provided tokenizer from Assignment 3 (GCP part) to do the 
        tokenization and remove stopwords. For example, a document 
        with a title that matches two distinct query words will be ranked before a 
        document with a title that matches only one distinct query word, 
        regardless of the number of times the term appeared in the title (or 
        query). 

        Test this by navigating to the a URL like:
         http://YOUR_SERVER_DOMAIN/search_title?query=hello+world
        where YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of ALL (not just top 100) search results, ordered from best to 
        worst where each element is a tuple (wiki_id, title).
    '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    # BEGIN SOLUTION
    query_tokens = tokenize(query)
    
    if index_title is None:
        return jsonify([])

    scores = Counter()
    
    # Determine base_dir and bucket_name for title index
    base_dir = 'postings_title'
    bucket_name = Config.BUCKET_NAME if not os.path.exists(os.path.join('data', base_dir)) else None
    if bucket_name is None:
        base_dir = os.path.join('data', base_dir)

    for token in query_tokens:
        if token in index_title.df:
            try:
                posting_list = index_title.read_a_posting_list(base_dir, token, bucket_name)
                for doc_id, tf in posting_list:
                    scores[doc_id] += 1
            except:
                pass
    
    # Sort by score desc
    sorted_scores = scores.most_common()
    
    # Map to (wiki_id, title)
    res = [(str(doc_id), id_to_title.get(str(doc_id), str(doc_id))) for doc_id, score in sorted_scores]
    # END SOLUTION
    return jsonify(res)

@app.route("/search_anchor")
def search_anchor():
    ''' Returns ALL (not just top 100) search results that contain A QUERY WORD 
        IN THE ANCHOR TEXT of articles, ordered in descending order of the 
        NUMBER OF QUERY WORDS that appear in anchor text linking to the page. 
        DO NOT use stemming. DO USE the staff-provided tokenizer from Assignment 
        3 (GCP part) to do the tokenization and remove stopwords. For example, 
        a document with a anchor text that matches two distinct query words will 
        be ranked before a document with anchor text that matches only one 
        distinct query word, regardless of the number of times the term appeared 
        in the anchor text (or query). 

        Test this by navigating to the a URL like:
         http://YOUR_SERVER_DOMAIN/search_anchor?query=hello+world
        where YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of ALL (not just top 100) search results, ordered from best to 
        worst where each element is a tuple (wiki_id, title).
    '''
    res = []
    query = request.args.get('query', '')
    if len(query) == 0:
      return jsonify(res)
    # BEGIN SOLUTION
    query_tokens = tokenize(query)
    
    if index_anchor is None:
        return jsonify([])

    scores = Counter()
    
    # Determine base_dir and bucket_name for anchor index
    base_dir = 'postings_anchor'
    bucket_name = Config.BUCKET_NAME if not os.path.exists(os.path.join('data', base_dir)) else None
    if bucket_name is None:
        base_dir = os.path.join('data', base_dir)

    for token in query_tokens:
        if token in index_anchor.df:
            try:
                posting_list = index_anchor.read_a_posting_list(base_dir, token, bucket_name)
                for doc_id, tf in posting_list:
                    scores[doc_id] += 1
            except:
                pass
    
    # Sort by score desc
    sorted_scores = scores.most_common()
    
    # Map to (wiki_id, title)
    res = [(str(doc_id), id_to_title.get(str(doc_id), str(doc_id))) for doc_id, score in sorted_scores]
    # END SOLUTION
    return jsonify(res)

@app.route("/get_pagerank", methods=['POST'])
def get_pagerank():
    ''' Returns PageRank values for a list of provided wiki article IDs. 

        Test this by issuing a POST request to a URL like:
          http://YOUR_SERVER_DOMAIN/get_pagerank
        with a json payload of the list of article ids. In python do:
          import requests
          requests.post('http://YOUR_SERVER_DOMAIN/get_pagerank', json=[1,5,8])
        As before YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of floats:
          list of PageRank scores that correrspond to the provided article IDs.
    '''
    res = []
    wiki_ids = request.get_json()
    if len(wiki_ids) == 0:
      return jsonify(res)
    # BEGIN SOLUTION
    for wiki_id in wiki_ids:
        # Convert to int if necessary, depending on how keys are stored
        # Assuming keys are ints or strings. Let's try both.
        val = page_rank.get(wiki_id)
        if val is None:
            try:
                val = page_rank.get(int(wiki_id))
            except:
                pass
        if val is None:
            try:
                val = page_rank.get(str(wiki_id))
            except:
                pass
        
        res.append(val if val is not None else 0.0)
    # END SOLUTION
    return jsonify(res)

@app.route("/get_pageview", methods=['POST'])
def get_pageview():
    ''' Returns the number of page views that each of the provide wiki articles
        had in August 2021.

        Test this by issuing a POST request to a URL like:
          http://YOUR_SERVER_DOMAIN/get_pageview
        with a json payload of the list of article ids. In python do:
          import requests
          requests.post('http://YOUR_SERVER_DOMAIN/get_pageview', json=[1,5,8])
        As before YOUR_SERVER_DOMAIN is something like XXXX-XX-XX-XX-XX.ngrok.io
        if you're using ngrok on Colab or your external IP on GCP.
    Returns:
    --------
        list of ints:
          list of page view numbers from August 2021 that correrspond to the 
          provided list article IDs.
    '''
    res = []
    wiki_ids = request.get_json()
    if len(wiki_ids) == 0:
      return jsonify(res)
    # BEGIN SOLUTION
    for wiki_id in wiki_ids:
        val = page_views.get(wiki_id)
        if val is None:
            try:
                val = page_views.get(int(wiki_id))
            except:
                pass
        if val is None:
            try:
                val = page_views.get(str(wiki_id))
            except:
                pass
        
        res.append(val if val is not None else 0)
    # END SOLUTION
    return jsonify(res)

def run(**options):
    app.run(**options)

if __name__ == '__main__':
    # run the Flask RESTful API, make the server publicly available (host='0.0.0.0') on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)
