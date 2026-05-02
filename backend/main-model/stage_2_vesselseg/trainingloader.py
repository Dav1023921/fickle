# This code will generate the training data for stage_3
from featureextractor import load_feature_extractor, get_combined_features
from utilities import make_all_instance_crops_training, compute_relative_morphology
import os
import numpy as np
from PIL import Image


#### SAME AS CORDSEG BUT WITH DIFFERENT PATHS AND COLOR MAP

color_map = {
    (0, 0, 0): 0, # Background
    (255,53,94) : 1, # Artery
    (53,21,212) : 2, # Vein
    (10, 10, 10): 0, # Ignore
}

def rgb_to_mask(mask_rgb):
    h, w, _ = mask_rgb.shape

    mask = np.zeros((h, w), dtype=np.int64)

    for color, class_id in color_map.items():
        matches = np.all(mask_rgb == np.array(color, dtype=np.uint8), axis=-1)
        mask[matches] = class_id

    return mask   

def generate_data_for_training():

    ### Get files
    img_dir  = "vessel-dataset/images"
    mask_dir = "vessel-dataset/masks"

    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".png")])

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
    
    all_instances = []

    for img_path, mask_path in zip(img_paths, mask_paths):
        image = np.array(Image.open(img_path).convert("RGB"))
        mask_rgb = Image.open(mask_path).convert("RGB")
        pred_mask = rgb_to_mask(np.array(mask_rgb))

        ### For each ground truth mask we generate the instance crops and morphology features
        instance_crops_artery = make_all_instance_crops_training(
            image=image,
            pred_mask=pred_mask,
            foreground_class=1,
            min_area=20,
        )
        instance_crops_vein = make_all_instance_crops_training(
            image=image,
            pred_mask=pred_mask,
            foreground_class=2,
            min_area=20,
        )

        instance_crops = instance_crops_artery + instance_crops_vein
        instance_crops = compute_relative_morphology(instance_crops)
        ### For each instance in the image, we get the combined features and label and add it to the all_instances list
        for item in instance_crops:
            ### Get the combined features (CNN features + morphology features)
            features = get_combined_features(item)
            all_instances.append({
                "features": features,
                "label": item["label"], # Assuming all instances are vessels for now
            })

    return all_instances

training_data = generate_data_for_training()

# training_data is a list of dicts with keys "features" and "label".

all_features = np.array([d["features"] for d in training_data])  # (N, 520)
all_labels = np.array([d["label"] for d in training_data])        # (N,)

np.save("features.npy", all_features)
np.save("labels.npy", all_labels)

