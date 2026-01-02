# Information Retrieval Project - Winter 2025-2026

## Project Overview
**Goal:** Build a search engine for English Wikipedia.
**Course:** 372-1-4406 Information Retrieval
**Semester:** Winter 2025-2026

This project is optional but meeting minimum requirements earns 10 points automatically. The project grade (15% weight) protects the exam grade.
Formula: `Exam grade = max(Exam, 0.85*Exam + 0.15*Project)`

## Data Sources
*   **Wikipedia Dump:** Entire English Wikipedia dump in a shared Google Storage bucket (same as Assignment #3).
*   **Pageviews:** You need to derive this (see code in Assignment #1).
*   **Queries:** `queries_train.json` contains queries and a ranked list of up to 100 relevant results for training (30 queries). Test split is not provided.

## Code Structure
The following starter code is provided:
*   `search_frontend.py`: Flask app for the search engine frontend. Contains six blank methods to implement.
*   `run_frontend_in_colab.ipynb`: Notebook for running the frontend in Colab for development and testing.
*   `run_frontend_in_gcp.sh`: Command-line instructions for deploying to GCP (Compute Engine instance, public IP).
*   `startup_script_gcp.sh`: Shell script to set up the Compute Engine instance. Modify only if additional packages are needed.
*   `inverted_index_gcp.py`: Code for reading/writing an index to GCP storage bucket.

## Minimum Requirements (Pass Grade: 56)
To pass, you must meet **ALL** of the following:
1.  **Functional Search Engine:** Process queries and return results from the entire corpus.
2.  **Testable Search Engine:** Accessible via a URL during the testing period (**Tuesday, Jan 13, 2025, 12:00 to Thursday, Jan 15, 2025, 12:00**).
3.  **Efficiency:** No query takes longer than **35 seconds**. Caching is **not allowed**.
4.  **Quality:** Average Precision@10 > 0.1 on the test set.
5.  **No External Services:** No dynamic API calls at query time. Static external packages/models are allowed (e.g., local vector DB).
6.  **Clean Code Repo:** Public GitHub (or similar) repo with a `README.md` explaining code structure and functionality.
7.  **Report:** Up to 4 pages (Hebrew or English) containing:
    *   Student IDs and emails.
    *   Link to GitHub repo.
    *   Link to public Google Storage Bucket with index data.
    *   List of index files with sizes (appendix).
    *   Description of key experiments, evaluation, and findings.
    *   Performance graphs (quality and time) for major versions.
    *   Qualitative evaluation of top 10 results for one good and one bad query.

## Full Requirements (for Full Grade)
In addition to minimum requirements:

### 1. Ranking Methods (10 points)
Implement 5 ranking methods in `search_frontend.py`. Max 35 seconds per query.
*   (a) Cosine similarity using tf-idf on article body.
*   (b) Binary ranking using article title.
*   (c) Binary ranking using anchor text.
*   (d) Ranking by PageRank.
*   (e) Ranking by article page views.

### 2. Efficiency (7 points)
Based on average retrieval time of the `search` method:
*   < 1s: 7 pts
*   1-1.5s: 6 pts
*   1.5-2s: 5 pts
*   2-2.5s: 4 pts
*   2.5-3s: 3 pts
*   3-3.5s: 2 pts
*   3.5-5s: 1 pt
*   > 5s: 0 pts

### 3. Results Quality (18 points)
Average across test queries of the harmonic mean of Precision@5 and F1@30, relative to other submissions.

### 4. Experimentation and Evaluation (15 points)
Additional experiments/retrieval models tried and their evaluation.

### 5. Reporting (4 points)
*   Clean code & clear explanations (2 pts).
*   Short presentation (3-5 slides) summarizing work (2 pts).

## Words of Advice
1.  Review Lecture #3 slides for cosine similarity ingredients.
2.  Review tf-idf calculation.
3.  Read Chapter 7 of the textbook for efficient retrieval techniques.
4.  Reserve some training queries for your own testing.
5.  Start with a small index derived from training queries for optimization, then scale up.
6.  The `search` method can use any technique (stemming, stopwords, embeddings, query expansion, etc.). Plan with your partner.
7.  Start small in Colab and build up. Test one thing at a time.
8.  Ensure early on that you can run the frontend on GCP without modifications.
9.  Leave 2-3 days for optimization on GCP.
10. Schedule regular work sessions with your partner.
