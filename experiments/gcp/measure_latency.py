import sys
import os
import json
import time
import argparse
import requests
import numpy as np
from datetime import datetime

# Path setup
# We assume this script is running from experiments/gcp/
# We need to find experiments/gcp/runs/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(BASE_DIR, "runs")
AGG_DIR = os.path.join(BASE_DIR, "aggregates")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "data")


def load_queries(path):
    """
    Loads queries from a JSON file.
    Expects a dictionary where keys are queries.

    Args:
        path (str): Path to the JSON file.

    Returns:
        dict: The loaded queries.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def measure_latency(base_url, queries_path, num_queries, repeat, version_name):
    """
    Measures the end-to-end latency of the search engine hosted at base_url.

    Performs the following:
    1. Loads queries.
    2. Selects a random subset.
    3. Sends requests sequentially (with repeats).
    4. Calculates Mean and Std Dev of latency.
    5. Saves results to JSON.

    Args:
        base_url (str): The root URL of the server (e.g. http://34.1.1.1:8080).
        queries_path (str): Path to queries_train.json.
        num_queries (int): Number of unique queries to sample.
        repeat (int): Number of times to repeat each query for stability.
        version_name (str): Label for the version being tested (for output files).
    """
    print(f"Measuring Latency for Version: {version_name}")
    print(f"Target: {base_url}")

    queries_data = load_queries(queries_path)
    all_queries = list(queries_data.keys())

    # Shuffle and pick subset if needed
    np.random.seed(42)
    selected_queries = np.random.choice(
        all_queries, size=min(len(all_queries), num_queries), replace=False
    )

    print(f"Testing with {len(selected_queries)} queries, {repeat} repeats per query.")

    latencies = []

    session = requests.Session()

    for i, q_text in enumerate(selected_queries):
        # Warmup (optional, maybe 1 request)
        pass

        query_latencies = []
        for _ in range(repeat):
            try:
                start = time.perf_counter()
                # Assuming /search?query=...
                resp = session.get(
                    f"{base_url}/search", params={"query": q_text}, timeout=30
                )
                resp.raise_for_status()
                # Force read content to ensure download completed
                _ = resp.content
                end = time.perf_counter()

                query_latencies.append((end - start) * 1000)  # ms
            except requests.RequestException as e:
                print(f"Request failed for query '{q_text}': {e}")

        if query_latencies:
            avg_q = np.mean(query_latencies)
            latencies.append(avg_q)
            print(f"Query {i+1}: {avg_q:.2f} ms")
        else:
            print(f"Query {i+1}: Failed")

    if not latencies:
        print("No successful measurements.")
        return

    mean_latency = np.mean(latencies)
    std_latency = np.std(latencies)

    print(f"\nFinal Results for {version_name}:")
    print(f"Mean Latency: {mean_latency:.2f} ms")
    print(f"Std Dev: {std_latency:.2f} ms")

    # Save Results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(RUNS_DIR, f"{timestamp}_{version_name}")
    os.makedirs(run_dir, exist_ok=True)

    result_data = {
        "version": version_name,
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "num_queries": len(selected_queries),
        "repeats": repeat,
        "mean_latency": mean_latency,
        "std_latency": std_latency,
        "per_query_latencies": latencies,
    }

    with open(os.path.join(run_dir, "latency.json"), "w") as f:
        json.dump(result_data, f, indent=4)

    # Also save to aggregates for easy plotting
    os.makedirs(AGG_DIR, exist_ok=True)
    agg_file = os.path.join(AGG_DIR, f"{version_name}_latency_agg.json")
    with open(agg_file, "w") as f:
        json.dump(result_data, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure GCP Latency")
    parser.add_argument(
        "--base_url",
        type=str,
        required=True,
        help="Base URL (e.g., http://34.1.1.1:8080)",
    )
    parser.add_argument(
        "--num_queries", type=int, default=30, help="Number of queries to sample"
    )
    parser.add_argument("--repeat", type=int, default=3, help="Repeats per query")
    parser.add_argument(
        "--version_name", type=str, default="gcp_v1", help="Version label"
    )

    # Try to find queries file automatically or take Arg
    default_q = os.path.join(DATA_DIR, "queries_train.json")
    parser.add_argument(
        "--queries_file", type=str, default=default_q, help="Path to queries_train.json"
    )

    args = parser.parse_args()

    measure_latency(
        args.base_url,
        args.queries_file,
        args.num_queries,
        args.repeat,
        args.version_name,
    )
