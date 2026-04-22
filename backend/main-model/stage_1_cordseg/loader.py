from utilities import make_all_instance_crops
import os
import numpy as np
from PIL import Image

# This file generates the crops of cords that will be used as training data for 
# the vessel segmentation model. 

color_map = {
    (0, 0, 0): 0, # Background
    (13, 4, 72): 1, # Cord
    (10, 10, 10): 0, # Ignore
}

output_dir = "training_cord_crops"
os.makedirs(output_dir, exist_ok=True)

def rgb_to_mask(mask_rgb):
    h, w, _ = mask_rgb.shape

    mask = np.zeros((h, w), dtype=np.int64)

    for color, class_id in color_map.items():
        matches = np.all(mask_rgb == np.array(color, dtype=np.uint8), axis=-1)
        mask[matches] = class_id

    return mask


def generate_cords_for_training():
    img_dir  = "new_images"
    mask_dir = "new_masks"

    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".jpg")])

    img_paths = []
    mask_paths = []
    for f in img_files:
        stem = os.path.splitext(f)[0]
        mask_path = os.path.join(mask_dir, stem + ".png")
        if os.path.exists(mask_path):
            img_paths.append(os.path.join(img_dir, f))
            mask_paths.append(mask_path)
        else:
            print("Missing mask for:", f)

    for img_path, mask_path in zip(img_paths, mask_paths):
        image = np.array(Image.open(img_path).convert("RGB"))
        mask_rgb = Image.open(mask_path).convert("RGB")
        pred_mask = rgb_to_mask(np.array(mask_rgb))

        instance_crops = make_all_instance_crops(
            image=image,
            pred_mask=pred_mask,
            foreground_class=1,
            min_area=20,
        )

        for item in instance_crops:
            stem = os.path.splitext(os.path.basename(img_path))[0]
            out = Image.fromarray(item["crop"])
            out.save(os.path.join(output_dir, f"{stem}_instance_{item['id']}_{item['size']}.png"))


generate_cords_for_training()