import os

class Config:
    PROJECT_ID = 'extreme-wind-480314-f5'
    BUCKET_NAME = 'yali-ir2025-bucket'
    
    # Path to the service account key file
    # Adjusted to look in the 'data' directory relative to project root
    KEY_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'extreme-wind-480314-f5-e88363037125.json'))
    
    # GCS Paths (Blob paths relative to bucket root)
    TEXT_INDEX_GCS = 'postings_gcp/index.pkl' 
    
    # Parquet directories in GCS
    ID_TO_TITLE_PARQUET_DIR_GCS = "mappings/id_to_title_parquet"
    TITLE_TO_ID_PARQUET_DIR_GCS = "mappings/title_to_id_parquet"
    
    # PageRank GCS Path
    PAGERANK_CSV_GZ_GCS = "pr/part-00000-a04c95dd-e3ce-4c9d-9d78-fa2201683fb3-c000.csv.gz"

    # Legacy fields (kept for compatibility)
    POSTING_GCP = f'gs://{BUCKET_NAME}/{TEXT_INDEX_GCS}'
    ID_TO_TITLE_PARQUET_DIR = f"gs://{BUCKET_NAME}/{ID_TO_TITLE_PARQUET_DIR_GCS}/"

    
