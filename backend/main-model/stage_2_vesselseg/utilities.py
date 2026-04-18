import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
from dataset import color_map
import torch.nn.functional as F
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cv2
from myunet import make_model
from PIL import Image
import os

output_dir = "instance_crops"
os.makedirs(output_dir, exist_ok=True)

IGNORE_RGB = (10, 10, 10)


def run_model(img):

    model = make_model()
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unet_resnet34.pth")
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    transform = T.Compose([T.ToTensor()])
    x = transform(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        probs = torch.sigmoid(logits)

    pred_mask = (probs > 0.5).squeeze().cpu().numpy().astype(np.uint8)
    confidence_map = probs.squeeze().cpu().numpy() 

    return img, logits, pred_mask, confidence_map

# Returns a dictionary of instances with their bounding boxes coordinates and masks
def semantic_to_instances(binary_mask, min_area=900):

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_mask.astype(np.uint8),
        connectivity=8
    )

    instances = []

    # loop over each blob excluding background 0
    for label_id in range(1, num_labels):
        x = stats[label_id, cv2.CC_STAT_LEFT]
        y = stats[label_id, cv2.CC_STAT_TOP]
        w = stats[label_id, cv2.CC_STAT_WIDTH]
        h = stats[label_id, cv2.CC_STAT_HEIGHT]
        area = stats[label_id, cv2.CC_STAT_AREA]

        if area < min_area:
            continue

        instance_mask = (labels == label_id).astype(np.uint8)

        # Compute morphology features from instance mask
        contours, _ = cv2.findContours(instance_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[0]
        perimeter = cv2.arcLength(cnt, True)
        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0
        aspect_ratio = w / h if h > 0 else 0

        # Simplify contour for Konva rendering
        epsilon = 0.005 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        polygon = approx.squeeze(1).flatten().tolist()

        instances.append({
            "id": label_id,
            "bbox": [x, y, x + w, y + h],
            "area": int(area),
            "mask": instance_mask,
            "width": w,
            "height": h,
            "centroid": centroids[label_id].tolist(),
            "perimeter": float(perimeter),
            "circularity": float(circularity),
            "aspect_ratio": float(aspect_ratio),
            "polygon": polygon,  # flat [x1, y1, x2, y2, ...] in mask space
    })
    return instances

# Given an instance_mask and bbox values and image get the crop
def make_instance_crop(image, instance_mask, bbox, ignore_rgb=IGNORE_RGB):

    x1, y1, x2, y2 = bbox

    # Create isolated copy of the image where only component pixels are visible
    isolated = np.full_like(image, ignore_rgb, dtype=np.uint8)
    isolated[instance_mask == 1] = image[instance_mask == 1]

    # Crop to bounding box
    crop = isolated[y1:y2, x1:x2]

    # Pad to square using longest dimension
    h, w = crop.shape[:2]
    crop_size = max(h, w)

    padded = np.full((crop_size, crop_size, 3), ignore_rgb, dtype=np.uint8)

    # Center the crop in the square canvas
    y_offset = (crop_size - h) // 2
    x_offset = (crop_size - w) // 2
    padded[y_offset:y_offset + h, x_offset:x_offset + w] = crop

    return padded, crop_size

from io import BytesIO
import base64

def get_instance_confidence(confidence_map, instance_mask):
    vessel_pixels = confidence_map[instance_mask == 1]
    if len(vessel_pixels) == 0:
        return 0.0
    return float(vessel_pixels.mean())

def get_instance_heatmap(confidence_map, instance_mask, bbox):
    x1, y1, x2, y2 = bbox
    h = y2 - y1
    w = x2 - x1
    crop_size = max(h, w)

    # crop confidence map to bbox region
    conf_crop = confidence_map[y1:y2, x1:x2]

    # pad to square
    heatmap = np.zeros((crop_size, crop_size), dtype=np.float32)
    y_offset = (crop_size - h) // 2
    x_offset = (crop_size - w) // 2
    heatmap[y_offset:y_offset + h, x_offset:x_offset + w] = conf_crop

    # mask out non-vessel pixels
    mask_crop = instance_mask[y1:y2, x1:x2]
    mask_padded = np.zeros((crop_size, crop_size), dtype=np.uint8)
    mask_padded[y_offset:y_offset + h, x_offset:x_offset + w] = mask_crop
    heatmap[mask_padded == 0] = 0

    # convert to colour
    heatmap_coloured = cm.jet(heatmap)[:, :, :3]
    heatmap_uint8 = (heatmap_coloured * 255).astype(np.uint8)

    img = Image.fromarray(heatmap_uint8)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

# Compute relative morphologies
def compute_relative_morphology(instances):
    if len(instances) == 0:
        return instances

    # Find the largest instance by area
    largest = max(instances, key=lambda x: x["area"])

    for inst in instances:
        inst["relative_area"]         = inst["area"]         / largest["area"]         if largest["area"] > 0 else 0
        inst["relative_perimeter"]    = inst["perimeter"]    / largest["perimeter"]    if largest["perimeter"] > 0 else 0
        inst["relative_circularity"]  = inst["circularity"]  / largest["circularity"]  if largest["circularity"] > 0 else 0
        inst["relative_aspect_ratio"] = inst["aspect_ratio"] / largest["aspect_ratio"] if largest["aspect_ratio"] > 0 else 0
        inst["num_vessels"] = len(instances)

    return instances

def make_all_instance_crops(image, pred_mask, confidence_map, foreground_class=1, min_area=2000):
    #create a binary mask and run connected components to get instance masks and bboxes
    binary_mask = (pred_mask == foreground_class).astype(np.uint8)
    instances = semantic_to_instances(binary_mask, min_area=min_area)
    instances = compute_relative_morphology(instances)

    # for each instance, make a fixed-size crop centered on the instance
    for inst in instances:
        crop, size = make_instance_crop(
            image=image,
            instance_mask=inst["mask"],
            bbox=inst["bbox"],
            ignore_rgb=IGNORE_RGB,
        )
        inst["crop"] = crop
        inst["confidence"] = get_instance_confidence(confidence_map, inst["mask"])
        inst["heatmap"] = get_instance_heatmap(confidence_map, inst["mask"], inst["bbox"])

    return instances

## Used for generating training data ################################
def make_all_instance_crops_training(image, pred_mask, foreground_class=None, min_area=2000):

    # create a binary mask and run connected components to get instance masks and bboxes
    binary_mask = (pred_mask == foreground_class).astype(np.uint8)
    instances = semantic_to_instances(binary_mask, min_area=min_area)

    # for each instance, make a fixed-size crop centered on the instance
    for inst in instances:
        crop, size = make_instance_crop(
            image=image,
            instance_mask=inst["mask"],
            bbox=inst["bbox"],
            ignore_rgb=IGNORE_RGB,
        )

        inst["crop"] = crop
        inst["num_vessels"] = len(instances)
        ### Here 1 is equal to the Artery and 0 is equal to the Vein.
        inst["label"] = 1 if foreground_class == 1 else 0

    return instances

def save_binary_mask(pred_mask, img_name, foreground_class=1):
    binary_mask = (pred_mask == foreground_class).astype(np.uint8) * 255  # no .cpu(), no .squeeze()
    mask_img = Image.fromarray(binary_mask)
    save_path = os.path.join(output_dir, f"binary_mask_{img_name}.png")  # .png extension
    mask_img.save(save_path)






# image, logits, pred_mask = run_model("case150_instance_1_512.png")

# image = np.array(Image.open("case150_instance_1_512.png").convert("RGB"))
# instances = make_all_instance_crops(image, pred_mask)


# for item in instances:
#     out = Image.fromarray(item["crop"])
#     out.save(os.path.join(output_dir, f"instance_{item['id']}.png"))

# print("pred_mask shape:", pred_mask.shape)
# print("unique values in pred_mask:", np.unique(pred_mask))
# print("logits shape:", logits.shape)
# print("logits min/max:", logits.min().item(), logits.max().item())

# save_binary_mask(pred_mask, "case150_instance_1", foreground_class=1)







# then 
# instances = make_all_instance_crops(image, pred_mask) this will contain everything that links everything together

#### Testing ############################################

# color_map = {
#     (0, 0, 0): 0, # Background
#     (255,53,94) : 1, # Artery
#     (53,21,212) : 1, # Vein
#     (10, 10, 10): 0, # Ignore
# }

# # image, logits, pred_mask = run_model("case247.jpg")

# image = np.array(Image.open("vessel-dataset/images/case0_instance_1_512.png").convert("RGB"))
# mask = Image.open("vessel-dataset/masks/case0_instance_1_512.png").convert("RGB")

# def rgb_to_mask(mask_rgb):
#     h, w, _ = mask_rgb.shape

#     mask = np.zeros((h, w), dtype=np.int64)

#     for color, class_id in color_map.items():
#         matches = np.all(mask_rgb == np.array(color, dtype=np.uint8), axis=-1)
#         mask[matches] = class_id

#     return mask

# pred_mask = rgb_to_mask(np.array(mask))

# instance_crops = make_all_instance_crops(
#             image=image,
#             pred_mask=pred_mask,
#             foreground_class=1,
#             min_area=20,
#         )

# for item in instance_crops:
#     out = Image.fromarray(item["crop"])
#     out.save(os.path.join(output_dir, f"instance_{item['id']}_{item['size']}.png"))