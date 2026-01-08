import pandas as pd

try:
    df = pd.read_parquet('data/sample.parquet')
    print("Columns:", df.columns)
    print("First row:", df.iloc[0])
except Exception as e:
    print(e)
