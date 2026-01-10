import matplotlib.pyplot as plt
import json
import glob
import os
import numpy as np

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGG_DIR = os.path.join(BASE_DIR, "aggregates")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")
GCP_AGG_DIR = os.path.join(os.path.dirname(BASE_DIR), "gcp", "aggregates")


def plot_report_graphs():
    """
    Generates the final comparison graphs for the report.

    Produces:
    1. performance_comparison.png: Bar chart of Mean P@10 for local versions.
    2. latency_comparison_gcp.png: Bar chart of Mean Latency for GCP versions.

    Reads from:
    - experiments/local/aggregates/*.json
    - experiments/gcp/aggregates/*.json
    """
    os.makedirs(PLOTS_DIR, exist_ok=True)

    # --- Graph F: Performance (P@10) per Version (Local Aggregates) ---
    json_files = glob.glob(os.path.join(AGG_DIR, "*_aggregate.json"))

    versions = []
    p10_means = []
    p10_stds = []

    for fpath in json_files:
        with open(fpath, "r") as f:
            data = json.load(f)
            versions.append(data.get("version", "unknown"))
            p10_means.append(float(data.get("mean_p10_avg", 0)))
            p10_stds.append(float(data.get("mean_p10_std", 0)))

    if versions:
        zipped = sorted(zip(versions, p10_means, p10_stds))
        vers, means, stds = zip(*zipped)

        x_pos = np.arange(len(vers))

        fig, ax = plt.subplots(figsize=(10, 6))

        # 1) Bars WITHOUT yerr
        rects = ax.bar(
            x_pos, means, align="center", alpha=0.7, color="lightgreen", zorder=2
        )

        # 2) Error bars explicitly
        ax.errorbar(
            x_pos,
            means,
            yerr=stds,
            fmt="none",
            ecolor="black",
            elinewidth=1.5,
            capsize=10,
            zorder=3,
            label="Std. Dev.",
        )

        ax.set_ylabel("Mean Precision@10")
        ax.set_title("Engine Performance per Version (Local)")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(vers)
        ax.yaxis.grid(True, zorder=0)
        ax.legend()

        # 3) Labels anchored to the mean (not to the errorbar cap)
        y_pad = max(0.005, 0.02 * max(means))  # small adaptive padding
        for x, m in zip(x_pos, means):
            ax.text(x, m + y_pad, f"{m:.3f}", ha="center", va="bottom")

        # Optional: headroom so label/errorbar won't touch top
        top = max(m + s for m, s in zip(means, stds))
        ax.set_ylim(0, top * 1.15)

        out_path = os.path.join(PLOTS_DIR, "performance_comparison.png")
        plt.tight_layout()
        plt.savefig(out_path)
        plt.close()
        print(f"Generated Performance Graph: {out_path}")
    else:
        print("No local aggregate files found for Graph F.")

    # --- Graph G: Latency per Version (GCP Aggregates) ---
    gcp_files = glob.glob(os.path.join(GCP_AGG_DIR, "*_latency_agg.json"))

    g_versions = []
    g_latencies = []
    g_stds = []

    for fpath in gcp_files:
        with open(fpath, "r") as f:
            data = json.load(f)
            g_versions.append(data.get("version", "unknown"))
            g_latencies.append(float(data.get("mean_latency", 0)))
            g_stds.append(float(data.get("std_latency", 0)))

    if g_versions:
        zipped_g = sorted(zip(g_versions, g_latencies, g_stds))
        vers_g, means_g, stds_g = zip(*zipped_g)

        x_pos_g = np.arange(len(vers_g))

        fig2, ax2 = plt.subplots(figsize=(10, 6))

        # 1) Bars WITHOUT yerr
        rects2 = ax2.bar(
            x_pos_g, means_g, align="center", alpha=0.7, color="salmon", zorder=2
        )

        # 2) Error bars explicitly
        ax2.errorbar(
            x_pos_g,
            means_g,
            yerr=stds_g,
            fmt="none",
            ecolor="black",
            elinewidth=1.5,
            capsize=10,
            zorder=3,
            label="Std. Dev.",
        )

        ax2.set_ylabel("Average Latency (ms)")
        ax2.set_title("Average Retrieval Time per Version (GCP Deployment)")
        ax2.set_xticks(x_pos_g)
        ax2.set_xticklabels(vers_g)
        ax2.yaxis.grid(True, zorder=0)
        ax2.legend()

        # 3) Labels anchored to the mean (not to the errorbar cap)
        y_pad_g = max(10.0, 0.02 * max(means_g))  # ms padding (min 10ms)
        for x, m in zip(x_pos_g, means_g):
            ax2.text(x, m + y_pad_g, f"{m:.0f}", ha="center", va="bottom")

        # Optional: headroom so label/errorbar won't touch top
        top_g = max(m + s for m, s in zip(means_g, stds_g))
        ax2.set_ylim(0, top_g * 1.15)

        out_path2 = os.path.join(PLOTS_DIR, "latency_comparison_gcp.png")
        plt.tight_layout()
        plt.savefig(out_path2)
        plt.close()
        print(f"Generated GCP Latency Graph: {out_path2}")
    else:
        print("No GCP latency aggregates found for Graph G.")


if __name__ == "__main__":
    plot_report_graphs()
