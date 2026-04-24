import os

img_dir = "dataset/Images"

img_files = sorted([f for f in os.listdir(img_dir)])
img_paths = []

print("Files in test_data:")
for f in img_files:
    print(f" - {f}")
    img_paths.append(os.path.join(img_dir, f))

