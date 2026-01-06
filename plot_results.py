import matplotlib.pyplot as plt
import json
import glob
import os
import numpy as np

OUTPUT_DIR = 'experiments'
PLOTS_DIR = os.path.join(OUTPUT_DIR, 'plots')

def plot_metrics():
    # 1. Setup
    if not os.path.exists(PLOTS_DIR):
        os.makedirs(PLOTS_DIR)

    json_files = glob.glob(os.path.join(OUTPUT_DIR, '*_metrics.json'))
    if not json_files:
        print("No metrics files found in 'experiments/' directory.")
        return

    versions = []
    maps = []
    p10s = []
    latencies = []

    # 2. Read Data
    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Use 'experiment' name as label, cleaning up formatting
            label = data.get('experiment', 'unknown').replace('_', ' ').title()
            versions.append(label)
            maps.append(data.get('map', 0))
            p10s.append(data.get('mean_p10', 0))
            latencies.append(data.get('mean_latency', 0))

    # Sort by version name to keep order consistent
    c = list(zip(versions, maps, p10s, latencies))
    c.sort()
    versions, maps, p10s, latencies = zip(*c)

    x_pos = np.arange(len(versions))
    width = 0.35

    # 3. Plot 1: Performance (MAP & Precision@10) - Requirement (f)
    fig, ax = plt.subplots(figsize=(10, 6))
    rects1 = ax.bar(x_pos - width/2, maps, width, label='MAP', color='skyblue')
    rects2 = ax.bar(x_pos + width/2, p10s, width, label='Precision@10', color='lightgreen')

    ax.set_ylabel('Score')
    ax.set_title('Engine Performance per Version')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(versions)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add text labels on bars
    ax.bar_label(rects1, padding=3, fmt='%.3f')
    ax.bar_label(rects2, padding=3, fmt='%.3f')

    plt.savefig(os.path.join(PLOTS_DIR, 'performance_comparison.png'))
    print(f"Saved performance graph to {PLOTS_DIR}/performance_comparison.png")
    plt.close()

    # 4. Plot 2: Average Retrieval Time - Requirement (g)
    fig, ax = plt.subplots(figsize=(8, 6))
    rects3 = ax.bar(x_pos, latencies, width, color='salmon', label='Avg Latency (s)')

    ax.set_ylabel('Time (seconds)')
    ax.set_title('Average Retrieval Time per Version')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(versions)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add passing threshold line (35s)
    ax.axhline(y=35, color='r', linestyle='--', label='Max Allowed (35s)')
    # Add bonus threshold line (1s)
    ax.axhline(y=1, color='g', linestyle='--', label='Bonus Goal (1s)')
    ax.legend()

    ax.bar_label(rects3, padding=3, fmt='%.2fs')

    plt.savefig(os.path.join(PLOTS_DIR, 'latency_comparison.png'))
    print(f"Saved latency graph to {PLOTS_DIR}/latency_comparison.png")
    plt.close()

if __name__ == "__main__":
    plot_metrics()
