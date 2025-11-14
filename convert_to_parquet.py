import pandas as pd

# Read the CSV file
df = pd.read_csv('crashdata2022-present.csv')

# Convert to Parquet
df.to_parquet('crashdata2022-present.parquet')

print("Conversion completed. File saved as crashdata2022-present.parquet")