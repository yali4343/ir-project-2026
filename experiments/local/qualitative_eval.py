import sys
import os
import json
import argparse

# Path setup
# Uses local engine so we need project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)

from query_engine import SearchEngine

def qualitative_eval(run_path, output_dir):
    print(f"Analyzing run: {run_path}")
    
    # 1. Load run results
    per_query_path = os.path.join(run_path, "per_query.jsonl")
    if not os.path.exists(per_query_path):
        print(f"Error: per_query.jsonl not found in {run_path}")
        return

    results = []
    with open(per_query_path, 'r') as f:
        for line in f:
            results.append(json.loads(line))
            
    if not results:
        print("No results found.")
        return

    # 2. Identify Best and Worst (using P@10 first, then AP@10)
    # Sort descending by P@10, then AP@10
    results.sort(key=lambda x: (x['p10'], x['ap10']), reverse=True)
    
    best_res = results[0]
    worst_res = results[-1]
    
    print(f"Best Query: '{best_res['query']}' (P@10={best_res['p10']})")
    print(f"Worst Query: '{worst_res['query']}' (P@10={worst_res['p10']})")
    
    # 3. Initialize Engine to get details
    print("Initializing Search Engine for detailed retrieval...")
    engine = SearchEngine()
    
    best_details = engine.search(best_res['query']) # returns list of (doc_id, title)
    worst_details = engine.search(worst_res['query'])
    
    # Take top 10
    best_top10 = best_details[:10]
    worst_top10 = worst_details[:10]
    
    # 4. Generate Report
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "qualitative_report.md")
    
    with open(report_path, 'w') as f:
        f.write("# Qualitative Evaluation Report\n\n")
        f.write(f"**Run Source:** {os.path.basename(run_path)}\n\n")
        
        f.write("## 1. Best Performing Query\n")
        f.write(f"**Query:** `{best_res['query']}`\n")
        f.write(f"**Metrics:** P@10: {best_res['p10']:.4f}, AP@10: {best_res['ap10']:.4f}\n\n")
        f.write("| Rank | Doc ID | Title |\n")
        f.write("|---|---|---|\n")
        for i, (doc_id, title) in enumerate(best_top10):
            t_str = title if title else "N/A"
            f.write(f"| {i+1} | {doc_id} | {t_str} |\n")
            
        f.write("\n**Analysis (What worked well):**\n")
        f.write("- [Place your analysis here]\n")
        f.write("- [e.g. Unique terms found in title...]\n\n")
        
        f.write("## 2. Poor Performing Query\n")
        f.write(f"**Query:** `{worst_res['query']}`\n")
        f.write(f"**Metrics:** P@10: {worst_res['p10']:.4f}, AP@10: {worst_res['ap10']:.4f}\n\n")
        f.write("| Rank | Doc ID | Title |\n")
        f.write("|---|---|---|\n")
        for i, (doc_id, title) in enumerate(worst_top10):
            t_str = title if title else "N/A"
            f.write(f"| {i+1} | {doc_id} | {t_str} |\n")
            
        f.write("\n**Analysis (What went wrong):**\n")
        f.write("- [Place your analysis here]\n")
        f.write("- [e.g. Ambiguous query, missing synonyms...]\n\n")
        
        f.write("## 3. Improvements\n")
        f.write("- [Suggestion 1]\n")
    
    print(f"Report generated at: {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Qualitative Report")
    parser.add_argument("--run_path", type=str, required=True, help="Path to a specific run folder (e.g. experiments/local/runs/timestamp_name)")
    parser.add_argument("--output_dir", type=str, default="experiments/local/qualitative", help="Output directory")
    
    args = parser.parse_args()
    
    qualitative_eval(args.run_path, args.output_dir)
