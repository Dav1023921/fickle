import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
from dataset import color_map
import torch.nn.functional as F
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cv2
from PIL import Image
import os

output_dir = "instance_crops"
os.makedirs(output_dir, exist_ok=True)

IGNORE_RGB = (10, 10, 10)


# Returns the original image, the raw model output (logits), and the predicted mask
def run_model(img):

    # open the image
    image_np = np.array(img)

    # make the model and load the state
    model = make_model()
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unet_resnet34.pth")
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    transform = T.Compose([
        T.ToTensor(),
    ])

    x = transform(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        preds = torch.argmax(logits, dim=1)
        probs = torch.softmax(logits, dim=1)

    pred_mask = preds[0].cpu().numpy().astype(np.uint8)

    # e.g. class 1 (foreground)
    confidence_map = probs[0, 1].cpu().numpy()  # shape: (H, W)

    return image_np, logits, pred_mask, confidence_map

# returns the mean probability within that instance region.
def get_instance_confidence(confidence_map, instance_mask):
    cord_pixels = confidence_map[instance_mask == 1]
    if len(cord_pixels) == 0:
        return 0.0
    return float(cord_pixels.mean())

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


        # Simplify contour for Konva rendering
        epsilon = 0.005 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        polygon = approx.squeeze(1).flatten().tolist()

        instances.append({
            "id": label_id,
            "bbox": [x, y, x + w, y + h],   # x2, y2 are slice-style bounds
            "mask": instance_mask,
            "polygon": polygon,
            "width": int(w),
            "height": int(h),
        })

    return instances

# Pad the image to 512x512 if it's smaller, using the specified fill value
def choose_crop_size(bbox, small_size=512, large_size=768):
    """
    Choose crop size based on bbox size.

    If the bbox fits inside 512, use 512.
    Otherwise use 768.
    """
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1

    if max(w, h) <= small_size:
        return small_size
    return large_size

from io import BytesIO
import base64

def get_instance_heatmap(confidence_map, instance_mask, bbox):
    x1, y1, x2, y2 = bbox
    
    # crop confidence map to bbox
    conf_crop = confidence_map[y1:y2, x1:x2]
    mask_crop = instance_mask[y1:y2, x1:x2]
    
    # mask out non-cord pixels
    heatmap = conf_crop.copy()
    heatmap[mask_crop == 0] = 0
    
    # convert to colour
    heatmap_coloured = cm.jet(heatmap)[:, :, :3]
    heatmap_uint8 = (heatmap_coloured * 255).astype(np.uint8)
    
    img = Image.fromarray(heatmap_uint8)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"

# Given an instance_mask and bbox values and image get the crop
def make_instance_crop(image, instance_mask, bbox, ignore_rgb=IGNORE_RGB):

    H, W = image.shape[:2]
    x1, y1, x2, y2 = bbox
    crop_size = choose_crop_size(bbox)

    # Create isolated an copy of the image where only component pixels are visible and the rest is ignore_rgb
    isolated = np.full_like(image, ignore_rgb, dtype=np.uint8)
    isolated[instance_mask == 1] = image[instance_mask == 1]

    # Center crop on component bbox center
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    crop_x1 = cx - crop_size // 2
    crop_y1 = cy - crop_size // 2
    crop_x2 = crop_x1 + crop_size
    crop_y2 = crop_y1 + crop_size

    # Source region from original image
    src_x1 = max(0, crop_x1)
    src_y1 = max(0, crop_y1)
    src_x2 = min(W, crop_x2)
    src_y2 = min(H, crop_y2)

    # Destination region inside fixed crop canvas
    dst_x1 = src_x1 - crop_x1
    dst_y1 = src_y1 - crop_y1
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    crop = np.full((crop_size, crop_size, 3), ignore_rgb, dtype=np.uint8)
    crop[dst_y1:dst_y2, dst_x1:dst_x2] = isolated[src_y1:src_y2, src_x1:src_x2]

    return crop, crop_size, crop_x1, crop_y1

# Return an array of dictionaries with the crops for each dict
def make_all_instance_crops(image, pred_mask, confidence_map, foreground_class=1, min_area=2000):

    # create a binary mask and run connected components to get instance masks and bboxes
    binary_mask = (pred_mask == foreground_class).astype(np.uint8)
    instances = semantic_to_instances(binary_mask, min_area=min_area)

    # for each instance, make a fixed-size crop centered on the instance


    for inst in instances:
        crop, size, crop_x1, crop_y1 = make_instance_crop(
            image=image,
            instance_mask=inst["mask"],
            bbox=inst["bbox"],
            ignore_rgb=IGNORE_RGB,
        )

        inst["crop"] = crop
        inst["size"] = size
        inst["crop_origin"] = (crop_x1, crop_y1) 
        inst["confidence"] = get_instance_confidence(confidence_map, inst["mask"])
        inst["heatmap"] = get_instance_heatmap(
            confidence_map,
            inst["mask"],
            inst["bbox"],
        )

    return instances

def generate_cord_polygons(
    pred_mask,
    foreground_class=1,
    min_area=20,
    epsilon_ratio=0.01,
):
    """
    Convert segmentation mask into simplified polygons for frontend (Konva).

    Returns:
        List of polygons, each as flat [x1, y1, x2, y2, ...]
    """

    # ---- Convert to numpy ----
    if hasattr(pred_mask, "cpu"):
        mask = pred_mask.cpu().numpy()
    else:
        mask = np.asarray(pred_mask)

    mask = mask.astype(np.uint8)

    # ---- Binary mask ----
    binary = (mask == foreground_class).astype(np.uint8) * 255

    # ---- Find contours ----
    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    polygons = []

    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue

        # ---- Simplify contour → polygon ----
        epsilon = epsilon_ratio * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # (N,1,2) → (N,2)
        pts = approx.squeeze(1)

        # Flatten → [x1, y1, x2, y2, ...]
        poly = pts.flatten().tolist()

        # Need at least 3 points (6 values)
        if len(poly) >= 6:
            polygons.append(poly)

    return polygons

def save_binary_mask(pred_mask, img_name, foreground_class=1):
    binary_mask = (pred_mask == foreground_class).astype(np.uint8) * 255
    mask_img = Image.fromarray(binary_mask)
    save_path = os.path.join(output_dir, f"binary_mask_{img_name}.png")
    mask_img.save(save_path)


# ## Testing
# image, logits, pred_mask = run_model("case_150_instance_1_.jpg")

# save_binary_mask(pred_mask, "case247", foreground_class=1)

# instance_crops = make_all_instance_crops(
#     image=image,
#     pred_mask=pred_mask,
#     foreground_class=1,
#     min_area=20,
# )

# for item in instance_crops:
#     out = Image.fromarray(item["crop"])
#     out.save(os.path.join(output_dir, f"instance_{item['id']}_{item['size']}.png"))   
