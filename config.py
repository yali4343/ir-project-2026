import os

class Config:
    PROJECT_ID = 'extreme-wind-480314-f5'
    BUCKET_NAME = 'yali-ir2025-bucket'
    # Path to the service account key file
    # Adjusted to look in the 'data' directory relative to project root
    KEY_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'extreme-wind-480314-f5-e88363037125.json'))
    
    
