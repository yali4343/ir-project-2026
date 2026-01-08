from google.cloud import storage
from config import Config

def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client.from_service_account_json(Config.KEY_FILE_PATH)
    blobs = storage_client.list_blobs(bucket_name)

    print(f"Blobs in {bucket_name}:")
    for blob in blobs:
        print(f"{blob.name} - {blob.size/1024/1024:.2f} MB")

if __name__ == "__main__":
    list_blobs(Config.BUCKET_NAME)
