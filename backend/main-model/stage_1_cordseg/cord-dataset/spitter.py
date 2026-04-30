import os
import shutil
import random

# --- Config ---
IMAGES_DIR = "Images"
MASKS_DIR  = "Masks"
OUTPUT_DIR = "split"
TRAIN_RATIO = 0.8
TEST_RATIO  = 0.2
SEED        = 42

# --- Get all image filenames ---
image_files = sorted([
    f for f in os.listdir(IMAGES_DIR)
    if f.lower().endswith(('.png', '.jpg'))
])

print(f"Total images found: {len(image_files)}")

# --- Shuffle reproducibly ---
random.seed(SEED)
random.shuffle(image_files)

# --- Calculate split indices ---
n = len(image_files)
n_test  = int(n * TEST_RATIO)
n_train = n - n_test

test_files  = image_files[:n_test]
train_files = image_files[n_test:]

print(f"Train: {len(train_files)} | Test: {len(test_files)}")

# --- Copy files into output folders ---
splits = {
    "train": train_files,
    "test":  test_files,
}

for split_name, files in splits.items():
    img_out  = os.path.join(OUTPUT_DIR, split_name, "images")
    mask_out = os.path.join(OUTPUT_DIR, split_name, "masks")
    os.makedirs(img_out,  exist_ok=True)
    os.makedirs(mask_out, exist_ok=True)

    for fname in files:
        # Copy image
        shutil.copy(
            os.path.join(IMAGES_DIR, fname),
            os.path.join(img_out, fname)
        )
        # Copy corresponding mask (assumes same filename)
        mask_fname = os.path.splitext(fname)[0] + ".png"

        shutil.copy(
            os.path.join(MASKS_DIR, mask_fname),
            os.path.join(mask_out, mask_fname)
        )

print("Done! Output structure:")
print(f"  {OUTPUT_DIR}/train/images & masks — {len(train_files)} files")
print(f"  {OUTPUT_DIR}/test/images  & masks — {len(test_files)} files")