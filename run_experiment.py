import json
import requests
import time
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime

# --- Configuration ---
QUERIES_FILE = 'data/queries_validation_split.json'
SEARCH_URL = 'http://localhost:8080/search'
OUTPUT_DIR = 'experiments'
EXPERIMENT_NAME = 'baseline_validation'

# --- Metrics Calculation ---

def recall_at_k(true_ids, predicted_ids, k):
    """Calculates Recall@k"""
    if not true_ids:
        return 0.0
    pred_k = predicted_ids[:k]
    relevant_retrieved = len(set(true_ids).intersection(set(pred_k)))
    return relevant_retrieved / len(true_ids)

def precision_at_k(true_ids, predicted_ids, k):
    """Calculates Precision@k"""
    if k == 0:
        return 0.0
    pred_k = predicted_ids[:k]
    relevant_retrieved = len(set(true_ids).intersection(set(pred_k)))
    return relevant_retrieved / k

def f1_at_k(true_ids, predicted_ids, k):
    """Calculates F1@k"""
    p = precision_at_k(true_ids, predicted_ids, k)
    r = recall_at_k(true_ids, predicted_ids, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)

def average_precision(true_ids, predicted_ids):
    """Calculates Average Precision (AP)"""
    if not true_ids:
        return 0.0
    
    score = 0.0
    num_hits = 0.0
    
    for i, p in enumerate(predicted_ids):
        if p in true_ids:
            num_hits += 1.0
            score += num_hits / (i + 1.0)
            
    return score / min(len(true_ids), len(predicted_ids)) # Normalized by possible hits in list or true count

def average_precision_standard(true_ids, predicted_ids):
    """Classic Average Precision for IR (dividing by total relevant)"""
    if not true_ids:
        return 0.0
    
    score = 0.0
    num_hits = 0.0
    
    true_set = set(true_ids)
    
    for i, p in enumerate(predicted_ids):
        if p in true_set:
            num_hits += 1.0
            score += num_hits / (i + 1.0)
            
    return score / len(true_ids)

# --- Experiment Runner ---

def run_experiment():
    print(f"Loading queries from {QUERIES_FILE}...")
    with open(QUERIES_FILE, 'r') as f:
        queries = json.load(f)
    
    results = []
    latencies = []
    aps = []
    p_at_10s = []
    
    print(f"Running {len(queries)} queries against {SEARCH_URL}...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    qualitative_log = open(f"{OUTPUT_DIR}/{EXPERIMENT_NAME}_qualitative.txt", "w", encoding="utf-8")
    
    for query_text, true_ids in queries.items():
        # Ensure true_ids are strings
        true_ids = [str(x) for x in true_ids]
        
        start_time = time.time()
        try:
            response = requests.get(SEARCH_URL, params={'query': query_text})
            response.raise_for_status()
            search_res = response.json()
        except Exception as e:
            print(f"Error querying '{query_text}': {e}")
            search_res = []
            
        latency = time.time() - start_time
        latencies.append(latency)
        
        # Extract returned IDs
        predicted_ids = [str(x[0]) for x in search_res]
        predicted_titles = [x[1] for x in search_res]
        
        # Metrics
        ap = average_precision_standard(true_ids, predicted_ids)
        p10 = precision_at_k(true_ids, predicted_ids, 10)
        
        aps.append(ap)
        p_at_10s.append(p10)
        
        # Log to qualitative file
        qualitative_log.write(f"Query: {query_text}\n")
        qualitative_log.write(f"Latency: {latency:.4f}s | AP: {ap:.4f} | P@10: {p10:.4f}\n")
        qualitative_log.write(f"Top 5 Results: {list(zip(predicted_ids[:5], predicted_titles[:5]))}\n")
        qualitative_log.write("-" * 50 + "\n")
        
        print(f"Query: '{query_text}' | Latency: {latency:.3f}s | AP: {ap:.3f}")

    qualitative_log.close()
    
    # --- Summary ---
    mean_latency = np.mean(latencies)
    map_score = np.mean(aps)
    mean_p10 = np.mean(p_at_10s)
    
    summary = {
        "experiment": EXPERIMENT_NAME,
        "date": datetime.now().isoformat(),
        "mean_latency": mean_latency,
        "map": map_score,
        "mean_p10": mean_p10,
        "num_queries": len(queries)
    }
    
    print("\n" + "="*30)
    print("EXPERIMENT SUMMARY")
    print("="*30)
    print(f"MAP: {map_score:.4f}")
    print(f"Mean Precision@10: {mean_p10:.4f}")
    print(f"Mean Latency: {mean_latency:.4f}s")
    print("="*30)
    
    # Save Metrics
    with open(f"{OUTPUT_DIR}/{EXPERIMENT_NAME}_metrics.json", "w") as f:
        json.dump(summary, f, indent=4)
        
    print(f"Results saved to {OUTPUT_DIR}/{EXPERIMENT_NAME}_metrics.json")

if __name__ == "__main__":
    run_experiment()
