import pandas as pd
df = pd.read_csv("features.csv")
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
df.to_csv("features_shuffled.csv", index=False)