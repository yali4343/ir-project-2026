# Experiments & Evaluation

This folder contains the complete infrastructure for evaluating the search engine locally (Quality) and on GCP (Latency), satisfying report requirements f, g, and h.

---

## 1. Local Quality Evaluation (Graph F)
We verify the retrieval quality (Precision@10, MAP) locally using the training queries split (80/20).

### Run a Single Experiment
```bash
python experiments/local/run_experiment.py --experiment_name "baseline_v1"
```

### Run a Multi-Run Suite (Recommended)
To ensure stability, run a suite which executes the experiment multiple times with different seeds and aggregates the results.
```bash
python experiments/local/run_suite.py --version_name "baseline_v1" --num_runs 3
```
*Output:* `experiments/local/aggregates/baseline_v1_aggregate.json`

### Generate Performance Graph (Req. f)
After running suites for different versions (e.g., baseline, improved), generate the comparison graph:
```bash
python experiments/local/plot_report_graphs.py
```
*Output:* `experiments/local/plots/performance_comparison.png`

---

## 2. GCP Latency Evaluation (Graph G)
We measure real-world hydration latency by querying the deployed VM from the client side.

### Measure Latency
Run this script against your deployed VM URL:
```bash
python experiments/gcp/measure_latency.py --base_url "http://<VM_IP>:8080" --version_name "gcp_v1" --num_queries 30
```
*Output:* `experiments/gcp/runs/.../latency.json` and `experiments/gcp/aggregates/gcp_v1_latency_agg.json`

### Generate Latency Graph (Req. g)
Run the plotting script locally (it reads the GCP aggregate files):
```bash
python experiments/local/plot_report_graphs.py
```
*Output:* `experiments/local/plots/latency_comparison_gcp.png`

---

## 3. Qualitative Evaluation (Req. h)
To analyze specific query performance (Best vs. Worst):

1. Identify a run folder you want to analyze (e.g., from `experiments/local/runs/`).
2. Run the qualitative analysis tool:
   ```bash
   python experiments/local/qualitative_eval.py --run_path "experiments/local/runs/<TIMESTAMP>_baseline_v1_run1"
   ```
3. This generates a Markdown report with the top 10 results for the best and worst queries.
   *Output:* `experiments/local/qualitative/qualitative_report.md`
4. **Action:** Open this file and fill in the analysis sections ("What worked well", "What didn't").

---

## Folder Map
- `local/runs/`: Individual quality experiment results.
- `local/aggregates/`: Averaged quality stats (mean +/- std).
- `local/plots/`: Final graphs for the report.
- `gcp/runs/`: Individual latency test results.
- `gcp/aggregates/`: Averaged latency stats.
