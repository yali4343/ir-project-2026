# GCP VM Deployment Guide

This guide describes how to deploy the Search Engine to a Google Cloud Platform (GCP) VM instance. The application is designed to run efficiently on a VM by loading all necessary data (indexes, mappings, PageRank) directly from Google Cloud Storage (GCS), eliminating the need to upload large data files to the VM.

## Prerequisites

- A GCP Project: `extreme-wind-480314-f5`
- A GCS Bucket: `yali-ir2025-bucket`
- A VM Instance (e.g., e2-standard-2 or similar) running Debian or Ubuntu.
- SSH access to the VM.

## Deployment Steps

### 1. Preparing the Code

You do **NOT** need to upload the `data/` directory. Create a zip of the codebase excluding data and virtual environments:

```bash
# On your local machine
zip -r search_engine_deploy.zip . -x "data/*" "venv/*" "__pycache__/*" "*.git*" ".vscode/*"
```

### 2. Connect to the VM

SSH into your VM instance:

```bash
gcloud compute ssh <your-vm-name> --zone <your-zone>
# Or use the GCP Console SSH button
```

### 3. Setup Environment

Install Python, pip, and virtual environment tools:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
```

Upload `search_engine_deploy.zip` to the VM (using the Upload file button in SSH window or `gcloud compute scp`).

Unzip the code:

```bash
unzip search_engine_deploy.zip -d search_engine
cd search_engine
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 4. Configure & Run

Set the `INDEX_SOURCE` environment variable to `gcs` to force the application to load data from the bucket.

```bash
export INDEX_SOURCE=gcs
```

Run the application:

```bash
python3 search_frontend.py
```

The application will start up. Watch the logs. You should see messages like:
- `Loading text index (Source Mode: gcs)...`
- `Loaded id_to_title from GCS Parquet...`
- `Loaded PageRank from GCS...`
- `Pageviews missing (OK for VM)...`

### 5. Accessing the Service

If running on port 8080 (default in `search_frontend.py`), ensure you have a Firewall Rule allowing TCP traffic on port 8080.

**To Create a Firewall Rule:**
1. Go to VPC Network > Firewall.
2. Create Firewall Rule.
3. Targets: All instances in the network.
4. Source filter: IPv4 ranges `0.0.0.0/0`.
5. Protocols and ports: `tcp:8080`.

Access via: `http://<EXTERNAL_VM_IP>:8080`

## Configuration Details (config.py)
The application is pre-configured with the following GCS paths:
- **Project**: `extreme-wind-480314-f5`
- **Bucket**: `yali-ir2025-bucket`
- **Text Index**: `postings_gcp/index.pkl`
- **ID to Title**: `mappings/id_to_title_parquet/`
- **PageRank**: `pr/part-00000-a04c95dd-e3ce-4c9d-9d78-fa2201683fb3-c000.csv.gz`

## Troubleshooting

- **Permissions**: Ensure the VM's Service Account has `Storage Object Viewer` permissions on the bucket `yali-ir2025-bucket`.
- **Missing index**: If it says "Could not load index from bucket", check if `postings_gcp/index.pkl` exists in the bucket.
- **Missing mappings**: If it issues a warning about `id_to_title`, check `mappings/id_to_title_parquet/` folder in the bucket.
- **Verification**: You can verify access from the VM using:
  ```bash
  gsutil ls gs://yali-ir2025-bucket/postings_gcp/
  ```
