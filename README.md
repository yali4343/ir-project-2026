# IR Project Winter 2025 - Wikipedia Search Engine

**Submitters:**
- **Yali Katz** — ID: 211381009
- **Amit Dvash** — ID: 316127653

---

## A. Project Overview

This service is a web-based search engine built to query a Wikipedia-like corpus. It provides a simple user interface and an HTTP API to retrieve relevant documents based on text queries.

**Key Features:**
- **Search Logic:** Supports TF-IDF, Cosine Similarity, and PageRank integration.
- **Hybrid Data Loading:** Capable of running locally with downloaded data or on a minimal GCP VM instance by streaming data directly from Google Cloud Storage (GCS) using `google-cloud-storage` and `pandas`.
- **Frontend/Backend:** A Flask-based backend serving a clean HTML/JS frontend.
- **Comprehensive Evaluation:** Includes a full suite of scripts for measuring precision, recall breakdown, and real-world latency.

---

## B. Repository Structure

```
├── search_frontend.py          # Main Flask application and server entry point
├── query_engine.py             # Orchestrates the search logic (Text Search + PageRank)
├── inverted_index_gcp.py       # Core class for handling Inverted Index IO (Read/Write)
├── config.py                   # Configuration attributes (GCS buckets, Paths)
├── requirements.txt            # Python dependencies
├── README.md                   # This documentation
├── README_DEPLOY_VM.md         # Specific instructions for VM deployment
├── Backend/
│   ├── data_Loader.py          # Module to load indexes, PageRank (CSV.gz), and mappings (Parquet)
│   ├── ranking.py              # Implementation of scoring algorithms (TF-IDF, Term Count)
│   └── tokenizer.py            # Text processing and tokenization logic
├── Frontend/
│   ├── templates/index.html    # Main search page HTML
│   └── static/                 # CSS and JS files
├── data/                       # Local data folder (Optional/Empty on VM)
│   └── queries_train.json      # Training queries for local evaluation
└── experiments/
    ├── local/                  # Local Quality Evaluation
    │   ├── run_experiment.py   # Single run execution
    │   ├── run_suite.py        # Multi-run aggregation (Stability)
    │   ├── plot_report_graphs.py # Generates performance graphs (Req. f, g)
    │   ├── qualitative_eval.py # Generates qualitative report (Req. h)
    │   ├── runs/               # Experiment run outputs
    │   └── plots/              # Final graphs
    └── gcp/                    # GCP Latency Evaluation
        └── measure_latency.py  # Script for measuring HTTP latency of deployed VM
```

---

## C. Architecture & Data Flow

1.  **Request:** The user enters a query in the frontend, which sends a GET request to `/search?query=...`.
2.  **Tokenization:** The backend receives the query and passes it to `Backend.tokenizer`, which filters stopwords and regex-matches words.
3.  **Search & Ranking:**
    *   `query_engine.py` calls `Backend.ranking` to calculate TF-IDF scores based on the body index.
    *   Results are filtered (Index Elimination) based on unique term overlap (50% threshold).
    *   PageRank is fetched for candidate documents and integrated into the final score.
4.  **Mapping:** Resulting document IDs are mapped to titles using the loaded `id_to_title` dictionary.
5.  **Response:** A JSON list of `[doc_id, title]` pairs is returned to the frontend for rendering.

**Data Source Modes:**
The system uses an environment variable `INDEX_SOURCE` to determine where to load data from:
*   `auto` (default): Tries local `data/` folder first; falls back to GCS.
*   `gcs`: Forces loading from Google Cloud Storage (buckets).
*   `local`: Forces loading from local disk only.

*Note: Query results are computed on-the-fly and are not cached.*

---

## D. Backend Deep Dive

### 1. `Backend/data_Loader.py`
**Responsibility:** Handles the loading of static data structures (Indexes, PageRank, Mappings) into memory at startup.

*   **`load_index(index_type)`**: Loads the `InvertedIndex` object (`index.pkl`). If `INDEX_SOURCE=gcs`, it fetches the pickle from the configured GCS blob path.
*   **`load_id_to_title()`**: Loads the mapping from Doc ID to Title. In GCS mode, it downloads multiple `.parquet` files from the bucket, reads them into Pandas DataFrames, and concatenates them into a single dictionary.
*   **`load_pagerank()`**: Downloads a **gzipped CSV file** from GCS and parses it into a `{doc_id: rank}` dictionary.
*   **`load_pageviews()`**: Optional. Returns an empty dictionary if the file is missing, preventing startup failures on minimal VMs.

### 2. `Backend/ranking.py`
**Responsibility:** Implements the core mathematical scoring functions.

*   **`_get_posting_source(posting_list_dir)`**: Determines the correct read path. If `INDEX_SOURCE=gcs`, it directs the reader to the bucket name.
*   **`calculate_tfidf_score_with_dir(...)`**: Computes Cosine Similarity between the query and documents using TF-IDF weights. It reads posting lists efficiently using the `InvertedIndex` class.
*   **`calculate_unique_term_count(...)`**: Counts how many unique query terms appear in each document. This is used for "Index Elimination".

### 3. `Backend/tokenizer.py`
**Responsibility:** Text processing.

*   **`tokenize(text)`**: Uses regex `RE_WORD` to find words and filters out a frozen set of English stopwords.

---

## E. Experiments & Evaluation

The repository contains a full suite for generating the reports required for the project.

### 1. Quality Evaluation (Local)
Scripts are located in `experiments/local/`.
*   **Run Single Experiment:** `python experiments/local/run_experiment.py --experiment_name "v1_test"` (Calculates Mean P@10, AP@10).
*   **Run Suite (Stability):** `python experiments/local/run_suite.py --version_name "baseline_v1"` (Runs multiple seeds and aggregates results).
*   **Generate Graphs:** `python experiments/local/plot_report_graphs.py` (Creates `performance_comparison.png`).

### 2. Latency Evaluation (GCP)
Scripts are located in `experiments/gcp/`.
*   **Measure Latency:** `python experiments/gcp/measure_latency.py --base_url "http://<VM_IP>:8080"`
    *   This pings the deployed VM and measures client-side HTTP response time.
    *   Results are saved to `experiments/gcp/aggregates/` and plotted by the local plotting script.

### 3. Qualitative Evaluation
*   **Generate Report:** `python experiments/local/qualitative_eval.py --run_path "experiments/local/runs/<timestamp>_run"`
    *   Identifies best/worst queries and generates a Markdown template (`qualitative_report.md`) with the top 10 results for manual analysis.

---

## F. Deployment / Running Instructions

### 1. Run Locally
**Prerequisites:** Python 3.8+, `pip`.

```bash
# Install dependencies
pip install -r requirements.txt

# Run server (tries to load from local 'data/' folder first)
python search_frontend.py
```
Access at `http://127.0.0.1:8080`.

### 2. Run on GCP VM
**Goal:** Run without uploading data files, streaming everything from GCS.

1.  **SSH into VM:** `gcloud compute ssh <vm-name>`
2.  **Setup Code:** Upload the code (exclude `data/`), unzip, and install requirements.
3.  **Set Environment & Run:**
    ```bash
    export INDEX_SOURCE=gcs
    python search_frontend.py
    ```
4.  **Firewall:** Ensure your project has a firewall rule allowing TCP traffic on port **8080**.

**Access:** `http://<VM_EXTERNAL_IP>:8080`

For detailed step-by-step VM deployment, see [README_DEPLOY_VM.md](README_DEPLOY_VM.md).

---

## G. Troubleshooting

*   **403 Forbidden (GCS):** Ensure the VM's Service Account has `Storage Object Viewer` role on `yali-ir2025-bucket`.
*   **Pyarrow Error:** If loading mappings fails, ensure `pyarrow` is installed (`pip install pyarrow`).
*   **Server Starts but Search Fails:** Check logs. If `INDEX_SOURCE` is not set to `gcs`, it might be looking for local files.
*   **Connection Refused:** Verify the application is running (`ps aux | grep python`) and port 8080 is open in GCP Firewall rules.
