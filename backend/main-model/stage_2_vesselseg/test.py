import numpy as np

# Load the saved files
features = np.load("features.npy")
labels = np.load("labels.npy")

# Basic checks
print(f"Features shape: {features.shape}")      # should be (N, 520)
print(f"Labels shape: {labels.shape}")          # should be (N,)
print(f"Total samples: {len(labels)}")
print(f"Artery samples (1): {np.sum(labels == 1)}")
print(f"Vein samples (0): {np.sum(labels == 0)}")

# Check first 5 samples
print("\n--- First 5 samples ---")
for i in range(min(5, len(labels))):
    label_name = "artery" if labels[i] == 1 else "vein"
    cnn_features = features[i, :512]
    morphology = features[i, 512:]
    print(f"\nSample {i} — {label_name}")
    print(f"  CNN features (first 5): {cnn_features[:5]}")
    print(f"  Morphology features: {morphology}")
    print(f"  Any NaN: {np.any(np.isnan(features[i]))}")
    print(f"  Any Inf: {np.any(np.isinf(features[i]))}")