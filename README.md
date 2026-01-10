# IR Project Winter 2025 - Wikipedia Search Engine

**Submitters:**
- **Yali Katz** — ID: 211381009
- **Amit Dvash** — ID: 316127653

---

## A. Project Overview

This service is a web-based search engine built to query a Wikipedia-like corpus. It provides a simple user interface and an HTTP API to retrieve relevant documents based on text queries.

**Key Features:**
- **Advanced Search Logic (Version 2):** Incorporates BM25 ranking, Word2Vec query expansion for weak queries, and efficient candidate limiting.
- **Optimized Latency:** Uses heap-based top-K selection and two-stage retrieval to prevent latency spikes on broad queries.
- **Hybrid Data Loading:** Capable of running locally with downloaded data or on a minimal GCP VM instance by streaming data directly from Google Cloud Storage (GCS) using `google-cloud-storage` and `pandas`.
- **Frontend/Backend:** A Flask-based backend serving a clean HTML/JS frontend.
- **Comprehensive Evaluation:** Includes a full suite of scripts for measuring precision, recall breakdown, and real-world latency.

**Project Constraints Compliance:**
1.  **Efficiency:** No query exceeds 35 seconds (Average latency ~9.7s locally for V2).
2.  **No Result Caching:** Query results are computed on-the-fly. Only static data (indexes, PageRank) is loaded at startup.
3.  **No External Services:** All indices and models (including Word2Vec) are local.
4.  **Quality:** Mean AP@10 > 0.1 (Achieved ~0.423 with Version 2).

---

## B. Repository Structure

```
├── search_frontend.py          # Main Flask application and server entry point
├── query_engine.py             # Orchestrates the search logic (BM25 + PageRank + Expansion)
├── inverted_index_gcp.py       # Core class for handling Inverted Index IO (Read/Write)
├── config.py                   # Configuration attributes (GCS buckets, Paths)
├── requirements.txt            # Python dependencies
├── README.md                   # This documentation
├── README_DEPLOY_VM.md         # Specific instructions for VM deployment
├── Backend/
│   ├── data_Loader.py          # Module to load indexes, PageRank (CSV.gz), and mappings (Parquet)
│   ├── ranking.py              # Legacy scoring algorithms
│   ├── ranking_v2.py           # Optimized BM25 & Heap-based scoring
│   ├── semantic_expansion.py   # Word2Vec expansion logic
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
    │   ├── plot_report_graphs.py # Generates performance comparison graphs
    │   ├── plots/              # Final graphs (performance_comparison.png)
    │   └── aggregates/         # JSON results for Version 1 and Version 2
    └── gcp/                    # GCP Latency Evaluation
        └── measure_latency.py  # Script for measuring HTTP latency of deployed VM
```

---

## C. Architecture & Data Flow

1.  **Request:** The user enters a query in the frontend, which sends a GET request to `/search?query=...`.
2.  **Tokenization:** The backend receives the query and passes it to `Backend.tokenizer`. Stopwords are filtered.
3.  **Search & Ranking (Version 2 Pipeline):**
    *   **Query Expansion:** Detailed checks trigger Word2Vec expansion for weak queries (<=2 tokens).
    *   **Stage 1 (Candidate Limiting):** BM25 scores are calculated for relevant postings. A heap (`heapq.nlargest`) efficiently selects the top-N (e.g., 2000) candidates.
    *   **Stage 2 (Re-ranking):** Only the top candidates are re-scored by integrating PageRank values.
4.  **Mapping:** Resulting document IDs are mapped to titles using the loaded `id_to_title` dictionary only for the final top-100 results.
5.  **Response:** A JSON list of `[doc_id, title]` pairs is returned to the frontend.

**Data Source Modes:**
The system uses an environment variable `INDEX_SOURCE` to determine where to load data from:
*   `auto` (default): Tries local `data/` folder first; falls back to GCS.
*   `gcs`: Forces loading from Google Cloud Storage (buckets).
*   `local`: Forces loading from local disk only.

*Note: As per requirements, there is NO caching of query results. Static structures (Index, PageRank, ID map) are cached in memory at startup.*

---

## D. Backend Deep Dive

### 1. `query_engine.py` (Search Engine Core)
**Responsibility:** Implements the Version 2 retrieval pipeline.
*   **Startup:** Loads `text_index`, `pagerank`, `pageviews`, `id_to_title`, and the `Word2Vec` model.
*   **Search Flow:**
    *   Checks query length for expansion.
    *   Calls `Backend.ranking_v2.get_candidate_documents` for efficient retrieval.
    *   Normalizes scores and blends with PageRank (85% Text / 15% PR).
    *   Returns top 100 results.

### 2. `Backend/ranking_v2.py`
**Responsibility:** Optimized scoring for Version 2.
*   **`get_candidate_documents`**: Computes BM25 scores. Handles missing DL stats gracefully (fallback to robust TF-IDF). Uses a min-heap to keep only the top-K candidates, avoiding expensive full sorts.

### 3. `Backend/data_Loader.py`
**Responsibility:** Handles the loading of static data structures.
*   **`load_index`**: Loads the Inverted Index.
*   **`load_pagerank`**: Downloads/Parses PageRank CSV.
*   **`load_id_to_title`**: Concatenates Parquet files from GCS into a lookup dict.

---

## E. Experiments & Evaluation

We performed strict local and cloud-based evaluations to verify improvements.

### Results Summary
**Comparison (Version 1 Baseline -> Version 2):**
*   **Quality (Mean Precision@10):** Improved from **~0.35** (v1) to **~0.528** (v2).
*   **Quality (Mean AP@10):** Improved from **~0.269** (v1) to **~0.423** (v2).
*   **Local Latency:** Average latency dropped by ~50% (~17.6s - 25.8s in v1 vs **~8.3s - 11.5s** in v2).
*   **GCP Latency:** Averaged **~3.46s** on the deployed VM (see `latency_comparison_gcp.png`).

### Plots
Visual comparisons generated by the suite are available in `experiments/local/plots/`:
*   `performance_comparison.png`: Shows the significant jump in P@10 for Version 2.
*   `latency_comparison.png`: Side-by-side latency reduction.

### Running the Evaluation
To reproduce these results locally:
```bash
# Run the Version 2 Suite
python experiments/local/run_suite.py --version_name "version2" --num_runs 3

# Generate Plots
python experiments/local/plot_report_graphs.py
```

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


