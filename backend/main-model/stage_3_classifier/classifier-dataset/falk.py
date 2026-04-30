import numpy as np

features = np.load("features_copy.npy")
labels   = np.load("labels_copy.npy")

print("Total samples:", len(labels))
print("Arteries (label=1):", (labels == 1).sum())
print("Veins    (label=0):", (labels == 0).sum())