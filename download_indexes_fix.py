import os
from google.cloud import storage
from config import Config

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    try:
        storage_client = storage.Client.from_service_account_json(Config.KEY_FILE_PATH)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
        
        print(f"Downloading {source_blob_name} to {destination_file_name}...")
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded {source_blob_name}.")
    except Exception as e:
        print(f"Failed to download {source_blob_name}: {e}")

if __name__ == "__main__":
    # 1. Download Body Index
    download_blob(Config.BUCKET_NAME, 'postings_gcp/index.pkl', 'data/postings_gcp/index.pkl')
    
    # 2. Download Title Index
    download_blob(Config.BUCKET_NAME, 'postings_title/index.pkl', 'data/postings_title/index.pkl')
    
    # 3. Download Anchor Index
    download_blob(Config.BUCKET_NAME, 'postings_anchor/index.pkl', 'data/postings_anchor/index.pkl')
