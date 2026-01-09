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
│   ├── data_Loader.py          # Module to load indexes, PageRank, and mappings from Local or GCS
│   ├── ranking.py              # Implementation of scoring algorithms (TF-IDF, Term Count)
│   └── tokenizer.py            # Text processing and tokenization logic
├── Frontend/
│   ├── templates/
│   │   └── index.html          # Main search page HTML
│   └── static/
│       ├── css/
│       │   └── style.css       # Stylesheet for the UI
│       └── js/
│           └── app.js          # Client-side logic to fetch results and render UI
└── data/                       # Local data folder (Optional/Empty on VM)
```

---

## C. Architecture & Data Flow

1.  **Request:** The user enters a query in the frontend, which sends a GET request to `/search?query=...`.
2.  **Tokenization:** The backend receives the query and passes it to `Backend.tokenizer`, which filters stopwords and regex-matches words.
3.  **Search & Ranking:**
    *   `query_engine.py` calls `Backend.ranking` to calculate TF-IDF scores based on the body index.
    *   Results are filtered (Index Elimination) based on term overlap.
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
*   **`load_pagerank()`**: Downloads a gzipped CSV file from GCS and parses it into a `{doc_id: rank}` dictionary.
*   **`load_pageviews()`**: Optional. Returns an empty dictionary if the file is missing, preventing startup failures on minimal VMs.

### 2. `Backend/ranking.py`
**Responsibility:** Implements the core mathematical scoring functions.

*   **`_get_posting_source(posting_list_dir)`**: Determines the correct read path. If `INDEX_SOURCE=gcs`, it directs the reader to the bucket name.
*   **`calculate_tfidf_score_with_dir(...)`**: Computes Cosine Similarity between the query and documents using TF-IDF weights. It reads posting lists efficiently using the `InvertedIndex` class.
*   **`calculate_unique_term_count(...)`**: Counts how many unique query terms appear in each document. This is used for "Index Elimination" (filtering docs that don't match enough query terms).

### 3. `Backend/tokenizer.py`
**Responsibility:** Text processing.

*   **`tokenize(text)`**:
    *   Uses regex `RE_WORD` to find words.
    *   Filters out a frozen set of English stopwords.
    *   Returns a list of normalized tokens.

---

## E. Main Python Files

### `config.py`
Central repository for configuration constants, including:
*   `PROJECT_ID` & `BUCKET_NAME`.
*   GCS paths for indexes (`TEXT_INDEX_GCS`), mappings (`ID_TO_TITLE_PARQUET_DIR_GCS`), and PageRank (`PAGERANK_CSV_GZ_GCS`).

### `query_engine.py`
The "Brain" of the search service.
*   **`__init__`**: Calls `data_Loader` to load all necessary data into memory.
*   **`search(query)`**: The main entry point. Orchestrates tokenization, fetching of TF-IDF scores, normalization, integration of PageRank, and formatting of final results with titles.
*   **`search_body`**, **`search_title`**, **`search_anchor`**: Specific search methods (mostly placeholders or specific implementations depending on current requirements).

### `search_frontend.py`
The Flask web server application.
*   **Endpoints:**
    *   `/`: Serves the `index.html` UI.
    *   `/search`: JSON endpoint for the full search logic.
    *   `/search_body`, `/search_title`: JSON endpoints for specific indices.
*   **Port:** Runs on **8080** by default (standard for GCP App Engine/VM).

### `inverted_index_gcp.py`
A utility class provided to handle the specific binary format of the Inverted Index.
*   **Functionality:** Can read/write the index structure and posting lists.
*   **GCS Integration:** Contains logic (`_open`, `get_bucket`) to transparently read binary data from GCS blobs if a bucket name is provided, enabling the "no-download" architecture.

---

## F. Frontend Overview

*   **`templates/index.html`**: A clean, responsive HTML5 layout containing a search header, input box, and a results area.
*   **`static/js/app.js`**:
    *   Listens for search button clicks or 'Enter' keypress.
    *   Fetches data asynchronously from `/search`.
    *   Parses the JSON response (`[[id, title], ...]`) and dynamically builds the result list.
    *   Handles loading states and error messages.
*   **`static/css/style.css`**: Provides a modern look using a blue/grey color scheme (`--primary-color`), card-based result items, and hover effects.

---

## G. Deployment / Running Instructions

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

1.  **SSH into VM:**
    ```bash
    gcloud compute ssh <vm-name>
    ```
2.  **Setup Code:**
    Upload the code (exclude `data/`), unzip, and install requirements:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Set Environment & Run:**
    This tells the app to ignore local files and load from the bucket.
    ```bash
    export INDEX_SOURCE=gcs
    python search_frontend.py
    ```
4.  **Firewall:** Ensure your project has a firewall rule allowing TCP traffic on port **8080**.

**Access:** `http://<VM_EXTERNAL_IP>:8080`

---

## H. Troubleshooting

*   **403 Forbidden (GCS):**
    *   Ensure the VM's Service Account has `Storage Object Viewer` role on `yali-ir2025-bucket`.
*   **Pyarrow Error:**
    *   If loading mappings fails, ensure `pyarrow` is installed (`pip install pyarrow`) as it's required for `pd.read_parquet`.
*   **Server Starts but Search Fails:**
    *   Check logs. If `INDEX_SOURCE` is not set to `gcs`, it might be looking for local files that don't exist.
*   **Connection Refused:**
    *   Verify the application is running (`ps aux | grep python`).
    *   Verify port 8080 is open in the GCP Firewall rules.


