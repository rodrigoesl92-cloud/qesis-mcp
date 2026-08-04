import pandas as pd

SOURCE_CSV = r"C:\Users\Lenovo\OneDrive\Documents\INITIUM\Master IR & GE\Final Master Thesis\_DATABASE\csv_exports\_sources.csv"

try:
    df = pd.read_csv(SOURCE_CSV)
    print("Columns found:")
    for col in df.columns:
        print("-", col)
except FileNotFoundError:
    print(f"Error: File not found: {SOURCE_CSV}")
except Exception as e:
    print(f"Error reading CSV: {e}")