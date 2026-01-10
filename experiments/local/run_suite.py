import sys
import os
import json
import argparse
import numpy as np
import subprocess
from datetime import datetime

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUN_SCRIPT_PATH = os.path.join(BASE_DIR, "run_experiment.py")
AGG_DIR = os.path.join(BASE_DIR, "aggregates")


def run_suite(version_name, num_runs, seed_base, split_ratio):
    """
    Executes multiple runs of the local experiment to ensure statistical significance.
    Aggregates the results (Mean/Std of MAP, P@10, Latency) across runs.

    Args:
        version_name (str): Label for the version (e.g. 'baseline_v1').
        num_runs (int): How many times to repeat the experiment with different seeds.
        seed_base (int): Starting seed (increments by 1 for each run).
        split_ratio (float): Train/Test split ratio passed to run_experiment.
    """
    print(f"Starting Suite for version: {version_name}")
    print(f"Runs: {num_runs}, Seed Base: {seed_base}")

    metrics_list = []

    for i in range(num_runs):
        current_seed = seed_base + i
        experiment_name = f"{version_name}_run{i+1}"

        cmd = [
            sys.executable,
            RUN_SCRIPT_PATH,
            "--experiment_name",
            experiment_name,
            "--seed",
            str(current_seed),
            "--split_ratio",
            str(split_ratio),
        ]

        print(f"Executing run {i+1}/{num_runs}...")
        try:
            # We capture the output to verify completion, but run_experiment saves its own JSON
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            # We need to find the resulting metrics.json.
            # run_experiment saves to output_dir (default experiments/local/runs)
            # inside <timestamp>_<experiment_name>/metrics.json

            # Since timestamp is generated inside, we have to look for the most recently created folder
            # matching the experiment name or parse stdout if we modify run_experiment to print the path specificially.
            # However, looking for the latest folder in runs/ with that experiment name is reliable enough given immediate execution.

            runs_dir = os.path.join(BASE_DIR, "runs")
            # List dirs, filter by experiment_name in suffix, sort by time
            candidates = []
            for d in os.listdir(runs_dir):
                full_p = os.path.join(runs_dir, d)
                if os.path.isdir(full_p) and d.endswith(experiment_name):
                    candidates.append(full_p)

            if not candidates:
                print(f"Error: Could not find output directory for {experiment_name}")
                continue

            # Get latest
            latest_run_dir = max(candidates, key=os.path.getctime)
            metrics_path = os.path.join(latest_run_dir, "metrics.json")

            with open(metrics_path, "r") as f:
                data = json.load(f)
                metrics_list.append(data)

        except subprocess.CalledProcessError as e:
            print(f"Run {i+1} failed: {e.stderr}")

    # Aggregation
    if not metrics_list:
        print("No successful runs to aggregate.")
        return

    p10_values = [m["mean_p10"] for m in metrics_list]
    ap10_values = [m["mean_ap10"] for m in metrics_list]
    latency_values = [m["mean_latency"] for m in metrics_list]

    aggregate_data = {
        "version": version_name,
        "timestamp": datetime.now().isoformat(),
        "num_runs": len(metrics_list),
        "mean_p10_avg": float(np.mean(p10_values)),
        "mean_p10_std": float(np.std(p10_values)),
        "mean_ap10_avg": float(np.mean(ap10_values)),
        "mean_ap10_std": float(np.std(ap10_values)),
        "mean_latency_avg": float(np.mean(latency_values)),
        "mean_latency_std": float(np.std(latency_values)),
        "runs_included": [m["experiment"] for m in metrics_list],
    }

    # Save aggregate
    os.makedirs(AGG_DIR, exist_ok=True)
    out_file = os.path.join(AGG_DIR, f"{version_name}_aggregate.json")
    with open(out_file, "w") as f:
        json.dump(aggregate_data, f, indent=4)

    print(f"Suite Complete. Aggregated results saved to: {out_file}")
    print(
        f"Mean P@10: {aggregate_data['mean_p10_avg']:.4f} (+/- {aggregate_data['mean_p10_std']:.4f})"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Experiment Suite (Multi-run aggregation)"
    )
    parser.add_argument(
        "--version_name",
        type=str,
        required=True,
        help="Label for this version (e.g. baseline, v2_weights)",
    )
    parser.add_argument(
        "--num_runs", type=int, default=3, help="Number of runs to average"
    )
    parser.add_argument(
        "--seed_base", type=int, default=42, help="Starting random seed"
    )
    parser.add_argument(
        "--split_ratio", type=float, default=0.8, help="Train/Test split ratio"
    )

    args = parser.parse_args()

    run_suite(args.version_name, args.num_runs, args.seed_base, args.split_ratio)
