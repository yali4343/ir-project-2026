import matplotlib.pyplot as plt
import json
import glob
import os
import numpy as np
from datetime import datetime

# Script location: experiments/local/plot_results.py
# Paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(BASE_DIR, 'runs')
PLOTS_DIR = os.path.join(BASE_DIR, 'plots')

def plot_metrics():
    # 1. Setup
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)

    # Search for metrics.json in all subdirectories of RUNS_DIR
    json_pattern = os.path.join(RUNS_DIR, '*', 'metrics.json')
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        print(f"No experiment runs found in {RUNS_DIR}")
        return

    experiments = []

    # 2. Read Data
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                exp_name = data.get('experiment', 'unknown')
                timestamp = data.get('timestamp', 'N/A')
                # Parse timestamp for sorting
                if timestamp != 'N/A':
                    try:
                        dt = datetime.fromisoformat(timestamp)
                    except:
                        dt = datetime.min
                else:
                    dt = datetime.min
                    
                experiments.append({
                    'name': exp_name,
                    'dt': dt,
                    'p10': data.get('mean_p10', 0),
                    'ap10': data.get('mean_ap10', 0),
                    'latency': data.get('mean_latency', 0)
                })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Sort by timestamp
    experiments.sort(key=lambda x: x['dt'])
    
    names = [e['name'] for e in experiments]
    p10s = [e['p10'] for e in experiments]
    ap10s = [e['ap10'] for e in experiments]
    latencies = [e['latency'] for e in experiments]

    x_pos = np.arange(len(names))
    width = 0.35

    # 3. Plot 1: Performance (P@10 & AP@10)
    fig, ax = plt.subplots(figsize=(12, 6))
    if len(p10s) > 0:
        rects1 = ax.bar(x_pos - width/2, p10s, width, label='Precision@10 (Primary)', color='#4CAF50')
        rects2 = ax.bar(x_pos + width/2, ap10s, width, label='AP@10', color='#2196F3')

        ax.set_ylabel('Score')
        ax.set_title('Experiment Performance: Precision@10 vs AP@10')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.set_ylim(0, 1.0)

        # Add text labels
        ax.bar_label(rects1, padding=3, fmt='%.3f')
        ax.bar_label(rects2, padding=3, fmt='%.3f')

    plt.tight_layout()
    plot_path1 = os.path.join(PLOTS_DIR, 'performance_comparison.png')
    plt.savefig(plot_path1)
    print(f"Saved performance plot to {plot_path1}")
    plt.close()

    # 4. Plot 2: Latency
    fig, ax = plt.subplots(figsize=(10, 6))
    if len(latencies) > 0:
        rects3 = ax.bar(x_pos, latencies, width, color='#FFC107', label='Avg Latency (ms)')

        ax.set_ylabel('Latency (ms)')
        ax.set_title('Average Query Latency (Local)')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(names, rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.legend()

        ax.bar_label(rects3, padding=3, fmt='%.0f ms')
    
    plt.tight_layout()
    plot_path2 = os.path.join(PLOTS_DIR, 'latency_comparison.png')
    plt.savefig(plot_path2)
    print(f"Saved latency plot to {plot_path2}")
    plt.close()

if __name__ == "__main__":
    plot_metrics()
