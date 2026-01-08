import sys
import os
import pandas as pd
from collections import defaultdict, Counter
from pathlib import Path

# Add project root and other folders to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent / 'IR_Project' / 'Backend'))

from inverted_index_gcp import InvertedIndex, MultiFileWriter
from tokenizer import tokenize

# Ensure TUPLE_SIZE is consistent
TUPLE_SIZE = 6

def write_memory_index_to_disk(index, base_dir, name):
    """
    Writes the in-memory `_posting_list` of the index to disk using MultiFileWriter
    and updates `posting_locs`. Then writes the index metadata.
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing posting lists for {name} to {base_dir}...")
    
    # Use MultiFileWriter
    writer = MultiFileWriter(base_dir, name)
    try:
        # Sort terms
        sorted_terms = sorted(index._posting_list.keys())
        for term in sorted_terms:
            pl = index._posting_list[term]
            # Sort by doc_id
            pl.sort(key=lambda x: x[0])
            
            # Encode
            b = bytearray()
            for doc_id, tf in pl:
                b.extend(doc_id.to_bytes(4, 'big'))
                # TF is capped at 2^16 - 1
                if tf >= 65536:
                   tf = 65535
                b.extend(tf.to_bytes(2, 'big'))
            
            # Write to file
            locs = writer.write(b)
            index.posting_locs[term].extend(locs)
    finally:
        writer.close()
        
    print(f"Writing index metadata for {name}...")
    index.write_index(base_dir, name)

def build_indexes(parquet_path):
    print(f"Loading data from {parquet_path}...")
    df = pd.read_parquet(parquet_path)
    
    # --- Build Title Index ---
    print("Building Title Index...")
    title_index = InvertedIndex()
    
    for _, row in df.iterrows():
        doc_id = row['id']
        title = row['title']
        if title:
            tokens = tokenize(title)
            if tokens:
                title_index.add_doc(doc_id, tokens)
                
    write_memory_index_to_disk(title_index, 'data/postings_title', 'index')
    
    # --- Build Anchor Index ---
    print("Building Anchor Index...")
    anchor_index = InvertedIndex()
    
    # Anchor logic: TF = number of unique docs pointing to target with term.
    target_tokens = defaultdict(list)
    
    for _, row in df.iterrows():
        # source_doc_id = row['id'] # Not needed for counting, just need uniqueness
        anchors = row['anchor_text'] # List of dicts
        
        # Check if empty (handling lists and numpy arrays)
        if hasattr(anchors, 'size'): # numpy
             if anchors.size == 0: continue
        elif not anchors: # list
             continue

        # Group tokens by target_id for THIS source doc
        current_doc_targets = defaultdict(set)
        
        for anchor in anchors:
            target_id = anchor['id']
            text = anchor['text']
            tokens = tokenize(text)
            current_doc_targets[target_id].update(tokens)
            
        # Add unique tokens from this source doc to the global target list
        for target_id, unique_tokens in current_doc_targets.items():
            target_tokens[target_id].extend(list(unique_tokens))
            
    # Now add to index
    for target_id, tokens in target_tokens.items():
        anchor_index.add_doc(target_id, tokens)
        
    write_memory_index_to_disk(anchor_index, 'data/postings_anchor', 'index')
    
    # Note: We are NOT rebuilding Body index (text_index) as we assume the one in GCP is correct 
    # (or we use the one downloaded to data/postings_gcp).
    # However, to be consistent with the "Fix", we should ensure data/postings_title 
    # and data/postings_anchor exist.

if __name__ == "__main__":
    import nltk
    nltk.download('stopwords')
    
    parquet_file = 'data/sample.parquet'
    if not os.path.exists(parquet_file):
        print(f"Error: {parquet_file} not found. Run download_sample.py first.")
    else:
        build_indexes(parquet_file)
