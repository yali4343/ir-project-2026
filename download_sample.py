from google.cloud import storage
from config import Config
import os

def download_sample():
    blob_name = 'multistream15_part3_preprocessed.parquet'
    dest = 'data/sample.parquet'
    
    storage_client = storage.Client.from_service_account_json(Config.KEY_FILE_PATH)
    bucket = storage_client.bucket(Config.BUCKET_NAME)
    blob = bucket.blob(blob_name)
    
    print(f"Downloading {blob_name} to {dest}...")
    blob.download_to_filename(dest)
    print("Done.")

if __name__ == '__main__':
    download_sample()
