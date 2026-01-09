import sys
import os
import json
import time
import argparse
import random
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from query_engine import SearchEngine

def load_queries(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_metrics(relevant_ids, retrieved_ids, k=10):
    """
    Computes Precision@k and AP@k.
    """
    relevant_set = set(relevant_ids)
    retrieved_k = retrieved_ids[:k]
    
    # P@k
    intersection = 0
    for doc_id in retrieved_k:
        if doc_id in relevant_set:
            intersection += 1
    p_at_k = intersection / k
    
    # AP@k
    score = 0.0
    num_hits = 0.0
    
    for i, doc_id in enumerate(retrieved_k):
        if doc_id in relevant_set:
            num_hits += 1.0
            score += num_hits / (i + 1.0)
            
    # For AP@k, we usually divide by min(k, total_relevant) or just total_relevant 
    # depending on definition. For a top-k evaluation, dividing by k or hits is common.
    # However, standard AP definition divides by "total number of relevant documents".
    # Given the project scope, let's normalize by min(k, len(relevant_set)) to be fair for small rel sets,
    # or just stick to intersection size if 0.
    
    if not relevant_set:
        return 0.0, 0.0

    # Avoiding division by zero
    denominator = min(k, len(relevant_set))
    ap_at_k = score / denominator if denominator > 0 else 0.0
    
    return p_at_k, ap_at_k

def run_experiment(experiment_name, seed, split_ratio, max_queries, output_dir):
    print(f"Starting Experiment: {experiment_name}")
    print(f"Seed: {seed}, Split: {split_ratio}")
    
    # 1. Init Engine
    print("Initializing Search Engine...")
    engine = SearchEngine()
    
    # 2. Load Data
    queries_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'queries_train.json')
    data = load_queries(queries_path)
    all_queries = list(data.items())
    
    # 3. Split
    rng = random.Random(seed)
    rng.shuffle(all_queries)
    
    split_idx = int(len(all_queries) * split_ratio)
    train_queries = all_queries[:split_idx]
    test_queries = all_queries[split_idx:]
    
    print(f"Total Queries: {len(all_queries)}")
    print(f"Train/Test Split: {len(train_queries)}/{len(test_queries)}")
    
    # We use TEST set for evaluation usually, or we can evaluate on both.
    # The prompt implies running experiments, likely on the test/validation set to measure performance.
    # We'll run on the TEST split by default as that's standard for reporting metrics.
    target_queries = test_queries
    
    if max_queries:
        target_queries = target_queries[:max_queries]
        print(f"Limiting to first {max_queries} queries.")
        
    results = []
    latencies = []
    p10_list = []
    ap10_list = []
    
    print("Running queries...")
    for query_text, relevant_ids in target_queries:
        start_time = time.time()
        # Search returns list of (doc_id, title)
        search_res = engine.search(query_text)
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000 # ms
        retrieved_ids = [str(doc_id) for doc_id, _ in search_res]
        
        p10, ap10 = calculate_metrics(relevant_ids, retrieved_ids, k=10)
        
        results.append({
            "query": query_text,
            "p10": p10,
            "ap10": ap10,
            "latency": latency,
            "num_retrieved": len(retrieved_ids),
            "num_relevant": len(relevant_ids)
        })
        
        latencies.append(latency)
        p10_list.append(p10)
        ap10_list.append(ap10)
        
    # 4. Aggregate
    mean_p10 = np.mean(p10_list) if p10_list else 0.0
    mean_ap10 = np.mean(ap10_list) if ap10_list else 0.0
    mean_latency = np.mean(latencies) if latencies else 0.0
    
    metrics = {
        "experiment": experiment_name,
        "timestamp": datetime.now().isoformat(),
        "num_queries": len(results),
        "mean_p10": mean_p10,
        "mean_ap10": mean_ap10,
        "mean_latency": mean_latency,
        "seed": seed,
        "split_ratio": split_ratio
    }
    
    # 5. Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(output_dir, f"{timestamp}_{experiment_name}")
    os.makedirs(run_dir, exist_ok=True)
    
    # Save metrics
    with open(os.path.join(run_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=4)
        
    # Save per-query details
    with open(os.path.join(run_dir, "per_query.jsonl"), "w") as f:
        for res in results:
            f.write(json.dumps(res) + "\n")
            
    # Save log
    with open(os.path.join(run_dir, "run_log.md"), "w") as f:
        f.write(f"# Experiment Log: {experiment_name}\n\n")
        f.write(f"- Date: {metrics['timestamp']}\n")
        f.write(f"- Seed: {seed}\n")
        f.write(f"- Queries Run: {len(results)}\n")
        f.write(f"- Mean P@10: **{mean_p10:.4f}**\n")
        f.write(f"- Mean AP@10: {mean_ap10:.4f}\n")
        f.write(f"- Mean Latency: {mean_latency:.2f} ms\n")
        
    print(f"\nExperiment Complete.")
    print(f"Results saved to: {run_dir}")
    print(f"Mean P@10: {mean_p10:.4f}")
    print(f"Mean Latency: {mean_latency:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run IR Project Local Experiment")
    parser.add_argument("--experiment_name", type=str, required=True, help="Name of the experiment run")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split")
    parser.add_argument("--split_ratio", type=float, default=0.8, help="Train/Test split ratio (default 0.8)")
    parser.add_argument("--max_queries", type=int, default=None, help="Limit number of queries for testing")
    parser.add_argument("--output_dir", type=str, default="experiments/local/runs", help="Output directory")
    
    args = parser.parse_args()
    
    # Adjust output dir to be absolute or relative to script correctly
    if not os.path.isabs(args.output_dir):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        args.output_dir = os.path.join(base_dir, "runs")

    run_experiment(args.experiment_name, args.seed, args.split_ratio, args.max_queries, args.output_dir)
