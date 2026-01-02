# Information Retrieval Project - Winter 2025-2026

## Project Status (Jan 2, 2026)
**Current Milestone:** Feature Complete (Pending Data Generation)

### Implemented Features
*   **Search Body:** TF-IDF Cosine Similarity using `postings_gcp/`.
*   **Search Title:** Binary ranking using `postings_title/` (Logic implemented, index pending).
*   **Search Anchor:** Binary ranking using `postings_anchor/` (Logic implemented, index pending).
*   **PageRank & PageViews:** API endpoints implemented (Data pending).
*   **Testing:** End-to-end testing pipeline via `notebooks/run_frontend_in_colab.ipynb`.
*   **Data Handling:** Automatic generation of `id_to_title.pkl` from parquet files.

### Current Repository Structure
```text
.
├── src/
│   ├── search_frontend.py    # Main Flask application with ranking logic
│   ├── inverted_index_gcp.py # GCS-compatible index reader
│   └── config.py             # Configuration (Bucket name, Project ID)
├── notebooks/
│   └── run_frontend_in_colab.ipynb # Testing & Development environment
├── scripts/
│   ├── run_frontend_in_gcp.sh
│   └── startup_script_gcp.sh
├── data/                     # Local data cache (Ignored by Git)
└── requirements.txt          # Project dependencies
```

