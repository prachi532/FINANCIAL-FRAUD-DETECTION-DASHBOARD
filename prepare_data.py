
import pandas as pd

input_file = "PS_20174392719_1491204439457_log.csv"
output_file = "transactions_sample.csv"

# Read the large file in smaller chunks.
# This avoids loading the whole dataset into memory.
samples = []

for chunk in pd.read_csv(input_file, chunksize=250_000):
    samples.append(chunk.sample(frac=0.02, random_state=42))

sampled_data = pd.concat(samples, ignore_index=True)

# Keep a maximum of 100,000 sampled transactions.
sampled_data = sampled_data.sample(
    n=min(100_000, len(sampled_data)),
    random_state=42
).reset_index(drop=True)

sampled_data.to_csv(output_file, index=False)

print("Sample created successfully!")
print("Rows:", len(sampled_data))
print("Fraud transactions:", sampled_data["isFraud"].sum())
print(sampled_data["isFraud"].value_counts())
