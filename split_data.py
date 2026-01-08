import json
import random
import os

def split_queries(input_file, train_file, val_file, split_ratio=0.8, seed=42):
    """
    Splits the queries file into training and validation sets.
    """
    print(f"Reading from {input_file}...")
    with open(input_file, 'r') as f:
        queries = json.load(f)
    
    # Convert dict items to a list for shuffling
    items = list(queries.items())
    
    random.seed(seed)
    random.shuffle(items)
    
    split_idx = int(len(items) * split_ratio)
    train_items = items[:split_idx]
    val_items = items[split_idx:]
    
    train_data = dict(train_items)
    val_data = dict(val_items)
    
    print(f"Total queries: {len(items)}")
    print(f"Training queries: {len(train_data)}")
    print(f"Validation queries: {len(val_data)}")
    
    print(f"Saving to {train_file}...")
    with open(train_file, 'w') as f:
        json.dump(train_data, f, indent=4)
        
    print(f"Saving to {val_file}...")
    with open(val_file, 'w') as f:
        json.dump(val_data, f, indent=4)
    print("Done.")

if __name__ == "__main__":
    base_path = "data"
    input_path = os.path.join(base_path, "queries_train.json")
    train_path = os.path.join(base_path, "queries_train_split.json")
    val_path = os.path.join(base_path, "queries_validation_split.json")
    
    split_queries(input_path, train_path, val_path)
