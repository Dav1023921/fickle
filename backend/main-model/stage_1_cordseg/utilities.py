import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
import cv2
import os
from PIL import Image


IGNORE_RGB = (10, 10, 10)


# Returns the original image, the raw model output (logits), and the predicted mask
def run_model(img):
    # convert image to np array
    image_np = np.array(img)

    # make the model and load the state
    model = make_model()
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unet_resnet34.pth")
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    # convert to tensor and apply ImageNet normalisation to match training
    x = T.Compose([
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        preds = torch.argmax(logits, dim=1)

    pred_mask = preds[0].cpu().numpy().astype(np.uint8)

    return image_np, logits, pred_mask

# Returns a dictionary of instances with their bounding boxes coordinates and masks
def semantic_to_instances(binary_mask, min_area=900):
 
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
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

        # Get the mask for this particular instance
        instance_mask = (labels == label_id).astype(np.uint8)

        # First find the contours of the instance mask
        contours, _ = cv2.findContours(instance_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = contours[0]

        # Calculate Morphology features
        perimeter = cv2.arcLength(cnt, True)
        area = cv2.contourArea(cnt)

        # Calculate Feret diameter endpoints
        pts = cnt.squeeze()
        if len(pts.shape) == 1:
            pts = pts.reshape(-1, 2)
        pts_tensor = torch.from_numpy(pts).float()
        distances = torch.cdist(pts_tensor, pts_tensor)
        i, j = np.unravel_index(distances.argmax(), distances.shape)
        p1 = pts[i].tolist()
        p2 = pts[j].tolist()
        feret_diameter = float(distances[i, j])

        # Simplify contour for Konva rendering
        epsilon = 0.006 * perimeter
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        polygon = approx.squeeze(1).flatten().tolist()

        instances.append({
            "id": label_id,
            "bbox": [x, y, x + w, y + h],
            "mask": instance_mask,
            "polygon": polygon,
            "width": int(w),
            "height": int(h),
            # --- Feret Diameter
            "feret_diameter_px": round(feret_diameter, 2),
            "feret_p1": p1,
            "feret_p2": p2,
        })

    return instances

def make_instance_crop(image, instance_mask, bbox, ignore_rgb=IGNORE_RGB):

    H, W = image.shape[:2]
    x1, y1, x2, y2 = bbox
    crop_size = 512 

    isolated = np.full_like(image, ignore_rgb, dtype=np.uint8)
    isolated[instance_mask == 1] = image[instance_mask == 1]

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    bbox_w = x2 - x1
    bbox_h = y2 - y1
    natural_size = max(bbox_w, bbox_h, crop_size)

    crop_x1 = cx - natural_size // 2
    crop_y1 = cy - natural_size // 2
    crop_x2 = crop_x1 + natural_size
    crop_y2 = crop_y1 + natural_size

    src_x1 = max(0, crop_x1)
    src_y1 = max(0, crop_y1)
    src_x2 = min(W, crop_x2)
    src_y2 = min(H, crop_y2)

    dst_x1 = src_x1 - crop_x1
    dst_y1 = src_y1 - crop_y1
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    crop = np.full((natural_size, natural_size, 3), ignore_rgb, dtype=np.uint8)
    crop[dst_y1:dst_y2, dst_x1:dst_x2] = isolated[src_y1:src_y2, src_x1:src_x2]

    if natural_size != crop_size:
        crop = cv2.resize(crop, (crop_size, crop_size), interpolation=cv2.INTER_LINEAR)

    return crop, crop_size, crop_x1, crop_y1

# Return an array of dictionaries with the crops for each dict
def make_all_instance_crops(image, pred_mask, foreground_class=1, min_area=2000):

    binary_mask = (pred_mask == foreground_class).astype(np.uint8)
    instances = semantic_to_instances(binary_mask, min_area=min_area)

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

    return instances


# ─── main ───
# Runs the model on every image in cord-dataset/split/test/images and saves the prediction mask

if __name__ == "__main__":
    base       = os.path.dirname(os.path.abspath(__file__))
    input_dir  = os.path.join(base, "cord-dataset", "split", "test", "images")
    output_dir = os.path.join(base, "cord-dataset", "split", "test", "predictions")
    os.makedirs(output_dir, exist_ok=True)

    image_files = sorted([
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ])

    print(f"Found {len(image_files)} images in {input_dir}")

    for filename in image_files:
        img_path = os.path.join(input_dir, filename)
        print(f"Processing {filename}...")

        img = Image.open(img_path).convert("RGB")
        _, _, pred_mask = run_model(img)

        stem = os.path.splitext(filename)[0]
        save_path = os.path.join(output_dir, f"{stem}_pred.png")
        Image.fromarray((pred_mask * 255).astype(np.uint8)).save(save_path)
        print(f"  Saved prediction mask to {save_path}")

    print("Done.")

# output_dir = "instance_crops"

# def save_binary_mask(pred_mask, img_name, foreground_class=1):
#     binary_mask = (pred_mask == foreground_class).astype(np.uint8) * 255
#     mask_img = Image.fromarray(binary_mask)
#     save_path = os.path.join(output_dir, f"binary_mask_{img_name}.png")
#     mask_img.save(save_path)


# ## Testing

# output_dir = "instance_crops"
# os.makedirs(output_dir, exist_ok=True)

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
