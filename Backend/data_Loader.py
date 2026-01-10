import sys
import os
import pickle
import pandas as pd
from google.cloud import storage
import io

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inverted_index_gcp import InvertedIndex
from config import Config

# Global cache
_ID_TO_TITLE = None
_PAGERANK = None

def get_storage_client():
    """
    Creates and returns a Google Cloud Storage client.
    
    Returns:
        google.cloud.storage.Client: The GCS client.
    """
    return storage.Client(project=Config.PROJECT_ID)

def get_bucket():
    """
    Retrieves the GCS bucket object configured in Config.
    
    Returns:
        google.cloud.storage.Bucket: The GCS bucket.
    """
    client = get_storage_client()
    return client.bucket(Config.BUCKET_NAME)

def load_index(index_type):
    """
    Load an inverted index based on type ('text', 'title', 'anchor').
    Source controlled by INDEX_SOURCE env var ('local', 'gcs', 'auto').
    
    Args:
        index_type (str): The type of index to load ('text', 'title', 'anchor').
        
    Returns:
        InvertedIndex: The loaded inverted index object.
        
    Raises:
        ValueError: If index_type is unknown.
        RuntimeError: If loading fails when forced to GCS.
    """
    index_source = os.environ.get('INDEX_SOURCE', 'auto')
    
    # Specific directories for each index type
    dir_map = {
        'text': 'data/postings_gcp',
        'title': 'data/postings_title',
        'anchor': 'data/postings_anchor'
    }
    
    if index_type not in dir_map:
        raise ValueError(f"Unknown index type: {index_type}")
        
    local_base_dir = dir_map[index_type]
    
    # For GCS, text index is at postings_gcp/index.pkl
    bucket_base_dir = None
    if index_type == 'text':
        bucket_base_dir = 'postings_gcp'
    
    name = 'index'
    print(f"Loading {index_type} index (Source Mode: {index_source})...")

    # 1. Try Local
    if index_source in ['local', 'auto']:
        local_file = os.path.join(local_base_dir, f'{name}.pkl')
        if os.path.exists(local_file):
            print(f"Loading local index {name} from {local_base_dir}...")
            try:
                return InvertedIndex.read_index(local_base_dir, name)
            except Exception as e:
                print(f"Error loading local index {name} from {local_base_dir}: {e}")
                if index_source == 'local':
                    raise

    # 2. Try GCS
    if index_source in ['gcs', 'auto']:
        if bucket_base_dir:
            print(f"Attempting to load index from GCS: gs://{Config.BUCKET_NAME}/{bucket_base_dir}/{name}.pkl")
            try:
                return InvertedIndex.read_index(bucket_base_dir, name, Config.BUCKET_NAME)
            except Exception as e2:
                print(f"Could not load index from bucket: {e2}")
                if index_source == 'gcs':
                    raise
        else:
             if index_source == 'gcs':
                  # If we forced GCS but have no GCS path mapped for this index type
                  raise ValueError(f"No GCS path configured for index type '{index_type}'")

    if index_source == 'gcs':
        raise RuntimeError(f"Failed to load {index_type} index from GCS.")
        
    print(f"Warning: Could not load {index_type} index. Returning empty index.")
    return InvertedIndex()

def load_pagerank():
    """
    Loads PageRank data from local file or GCS.
    
    Global variable _PAGERANK is used as cache.
    
    Returns:
        dict: A dictionary mapping doc_id to PageRank score.
              Returns empty dict if loading fails.
    """
    global _PAGERANK
    if _PAGERANK is not None:
        return _PAGERANK

    index_source = os.environ.get('INDEX_SOURCE', 'auto')
    print(f"Loading PageRank (Source Mode: {index_source})...")

    # 1. Try Local
    if index_source in ['local', 'auto']:
        path = os.path.join('data', 'pagerank.pkl')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    _PAGERANK = pickle.load(f)
                print(f"Loaded local PageRank ({len(_PAGERANK)} entries).")
                return _PAGERANK
            except Exception as e:
                print(f"Error loading local pagerank: {e}")
                if index_source == 'local': raise

    # 2. Try GCS
    if index_source in ['gcs', 'auto']:
        try:
            print(f"Loading PageRank from GCS: gs://{Config.BUCKET_NAME}/{Config.PAGERANK_CSV_GZ_GCS}")
            bucket = get_bucket()
            blob = bucket.blob(Config.PAGERANK_CSV_GZ_GCS)
            content = blob.download_as_bytes()
            # Parse CSV (doc_id, rank)
            df = pd.read_csv(io.BytesIO(content), compression='gzip', header=None)
            _PAGERANK = dict(zip(df[0], df[1]))
            print(f"Loaded PageRank from GCS ({len(_PAGERANK)} entries).")
    """
    Loads page view data.
    Currently prefers local file.
    
    Returns:
        dict: A dictionary mapping doc_id to page views.
              Returns empty dict if not found.
    """
            return _PAGERANK
        except Exception as e:
            print(f"Error loading PageRank from GCS: {e}")
            if index_source == 'gcs': raise

    print("Warning: PageRank not found. Returning empty dict.")
    return {}

def load_pageviews():
    index_source = os.environ.get('INDEX_SOURCE', 'auto')
    # Pageviews - optional, local preferred if auto, GCS not explicitly configured in instructions but let's be safe.
    
    if index_source in ['local', 'auto']:
        path = os.path.join('data', 'pageviews.pkl')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
    """
    Loads the mapping from document ID to title.
    Supports loading from local pickle or GCS parquet files.
    
    Global variable _ID_TO_TITLE is used as cache.
    
    Returns:
        dict: A dictionary mapping doc_id to title string.
              Returns empty dict if loading fails.
    """
                    return pickle.load(f)
            except:
                pass
    
    print("Pageviews missing (OK for VM). Returning empty dict.")
    return {}

def load_id_to_title():
    global _ID_TO_TITLE
    if _ID_TO_TITLE is not None:
        return _ID_TO_TITLE

    index_source = os.environ.get('INDEX_SOURCE', 'auto')
    print(f"Loading id_to_title (Source Mode: {index_source})...")

    # 1. Try Local
    if index_source in ['local', 'auto']:
        path = os.path.join('data', 'id_to_title.pkl')
        if os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    _ID_TO_TITLE = pickle.load(f)
                print(f"Loaded local id_to_title ({len(_ID_TO_TITLE)} entries).")
                return _ID_TO_TITLE
            except Exception as e:
                print(f"Error loading local id_to_title: {e}")
                if index_source == 'local': raise

    # 2. Try GCS
    if index_source in ['gcs', 'auto']:
        try:
            print(f"Loading id_to_title from GCS Parquet: gs://{Config.BUCKET_NAME}/{Config.ID_TO_TITLE_PARQUET_DIR_GCS}")
            bucket = get_bucket()
            blobs = list(bucket.list_blobs(prefix=Config.ID_TO_TITLE_PARQUET_DIR_GCS))
            
            dfs = []
            for blob in blobs:
                if blob.name.endswith('.parquet'):
                    data = blob.download_as_bytes()
                    dfs.append(pd.read_parquet(io.BytesIO(data)))
            
            if dfs:
                full_df = pd.concat(dfs)
                # Assuming standard format: 'id', 'title'
                if 'id' in full_df.columns and 'title' in full_df.columns:
                    _ID_TO_TITLE = dict(zip(full_df['id'], full_df['title']))
                else:
                    _ID_TO_TITLE = dict(zip(full_df.iloc[:, 0], full_df.iloc[:, 1]))
                print(f"Loaded id_to_title from GCS ({len(_ID_TO_TITLE)} entries).")
                return _ID_TO_TITLE
            else:
                print("No parquet files found in GCS for id_to_title.")
        except Exception as e:
            print(f"Error loading id_to_title from GCS: {e}")
            if index_source == 'gcs': raise
            
    print("Warning: id_to_title not found. Returning empty dict.")
    return {}
