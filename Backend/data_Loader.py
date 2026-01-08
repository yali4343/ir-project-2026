import sys
import os
import pickle

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inverted_index_gcp import InvertedIndex
from config import Config

def load_index(index_type):
    """
    Load an inverted index based on type ('text', 'title', 'anchor').
    """
    # Specific directories for each index type
    dir_map = {
        'text': 'data/postings_gcp',
        'title': 'data/postings_title',
        'anchor': 'data/postings_anchor'
    }
    
    if index_type not in dir_map:
        raise ValueError(f"Unknown index type: {index_type}")
        
    local_base_dir = dir_map[index_type]
    bucket_base_dir = 'postings_gcp' if index_type == 'text' else f'postings_{index_type}'
    
    # The file is always named 'index' (loading index.pkl)
    name = 'index'
    
    print(f"Loading {index_type} index from {local_base_dir}...")
    
    # Try local first
    try:
        return InvertedIndex.read_index(local_base_dir, name)
    except Exception as e:
        print(f"Could not load local index {name} from {local_base_dir}: {e}")
        # Try bucket (only works for text currently as title/anchor are not in bucket)
        try:
            return InvertedIndex.read_index(bucket_base_dir, name, Config.BUCKET_NAME)
        except Exception as e2:
            print(f"Could not load index from bucket: {e2}")
            return InvertedIndex()

def load_pagerank():
    return load_dict('pagerank')

def load_pageviews():
    return load_dict('pageviews')

def load_id_to_title():
    return load_dict('id_to_title')

def load_dict(name):
    path = os.path.join('data', f'{name}.pkl')
    if os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading {name}: {e}")
    return {}
