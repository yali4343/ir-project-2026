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
    # All indices are now in data/postings_gcp as per instructions
    local_base_dir = 'data/postings_gcp' 
    bucket_base_dir = 'postings_gcp'
    
    name_map = {
        'text': 'text_index',
        'title': 'title_index',  
        'anchor': 'anchor_index'
    }
    
    if index_type not in name_map:
        raise ValueError(f"Unknown index type: {index_type}")
        
    name = name_map[index_type]
    print(f"Loading {index_type} index ({name})...")
    
    # Try local first
    try:
        return InvertedIndex.read_index(local_base_dir, name)
    except Exception as e:
        print(f"Could not load local index {name}: {e}")
        # Try bucket
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
