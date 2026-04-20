import os
import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# ── config ───────────────────────────────────────────────────────────────────
IMAGE_FOLDER   = "images"
OUTPUT_FOLDER  = "output"
REFERENCE_IMAGE = "images/case200.jpg"
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

img_paths = sorted([
    os.path.join(IMAGE_FOLDER, f)
    for f in os.listdir(IMAGE_FOLDER)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
])

print("Found images:", img_paths)

def reinhard_normalise(source, target):
    source_lab = cv2.cvtColor(source, cv2.COLOR_RGB2LAB).astype(float)
    target_lab = cv2.cvtColor(target, cv2.COLOR_RGB2LAB).astype(float)
    for i in range(3):
        source_lab[:,:,i] = (source_lab[:,:,i] - source_lab[:,:,i].mean()) \
                           / (source_lab[:,:,i].std() + 1e-6) \
                           * target_lab[:,:,i].std() \
                           + target_lab[:,:,i].mean()
    return cv2.cvtColor(np.clip(source_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB)

# Load reference
reference = np.array(Image.open(REFERENCE_IMAGE).convert("RGB"))

for img_path in img_paths:
    print(f"Processing: {img_path}")
    original  = np.array(Image.open(img_path).convert("RGB"))

    try:
        normalised = reinhard_normalise(original, reference)
    except Exception as e:
        print(f"Skipping {img_path}: {e}")
        continue

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    axes[0].imshow(original);   axes[0].set_title("Before"); axes[0].axis("off")
    axes[1].imshow(normalised); axes[1].set_title("After");  axes[1].axis("off")
    plt.tight_layout()

    out_name = os.path.splitext(os.path.basename(img_path))[0] + "_comparison.png"
    plt.savefig(os.path.join(OUTPUT_FOLDER, out_name), dpi=150)
    plt.close()
    print(f"Saved: {out_name}")

print("Done!")