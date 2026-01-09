# Experiment Log

| Experiment | Description | Precision@10 | Latency (s) | Improvements/Changes |
|------------|-------------|--------------|-------------|----------------------|
| Baseline (Validation) | Initial config | 0.3167 | 16.33s | text=0.5, title=0.5, anchor=0.4, pr=0.1 (Unnormalized) |
| Experiment 2 (Soft AND + High PR) | Index Elimination (Min 50% term match) + Weights: Text=0.3, Title=0.4, Anchor=0.3, PR=0.5 | **0.3833** (+21%) | 25.56s | Filtered out ~90% of candidates (noise reduction) |
