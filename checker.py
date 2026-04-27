import faiss
import numpy as np
import pandas as pd
import pickle


index = faiss.read_index("vector_db/index.faiss")

with open("vector_db/index.pkl", "rb") as f:
    metadata = pickle.load(f)

if isinstance(metadata, list):
    if len(metadata) > 0 and isinstance(metadata[0], dict):
        meta_df = pd.DataFrame(metadata)
    else:
        meta_df = pd.DataFrame({"text": metadata})
elif isinstance(metadata, dict):
    meta_df = pd.DataFrame([metadata])
else:
    meta_df = pd.DataFrame(metadata)

n = index.ntotal
d = index.d

vectors = np.zeros((n, d), dtype="float32")

for i in range(n):
    vectors[i] = index.reconstruct(i)

vec_df = pd.DataFrame(vectors, columns=[f"dim_{i}" for i in range(d)])

final_df = pd.concat([meta_df, vec_df], axis=1)


final_df.to_csv("faiss_export_new.csv", index=False)

print("✅ Exported to faiss_export_new.csv")