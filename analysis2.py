import os
import shutil

present = {0,1,4,13,19,23,24,26,30,32,33,37,49,70,71,72,73,74,75,77,78,80,81,82,84,85,89,90,93,94,95,96,97,98,99,101,103,104,112,116,118,120,125,126,128,131,132,150,165,169,175,176,178,180,185,186,187,196,197,203,205,220,226,232,247}
missing = [i for i in range(270) if i not in present]

src_dir = "cord"
output_dir = "test_data_new"

os.makedirs(output_dir, exist_ok=True)

for num in missing:
    filename = f"case{num}.jpg"
    src_path = os.path.join(src_dir, filename)
    dst_path = os.path.join(output_dir, filename)
    if os.path.exists(src_path):
        shutil.copy(src_path, dst_path)
    else:
        print(f"Warning: {filename} not found in {src_dir}")

print(f"Done. Total files in output: {len(os.listdir(output_dir))}")