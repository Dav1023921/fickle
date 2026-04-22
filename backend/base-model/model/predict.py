from io import BytesIO

from PIL import Image
import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
from dataset import color_map
import torch.nn.functional as F
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import cv2

cls_to_rgb = {
    0: (0, 0, 0),
    1: (56, 37, 158),
    2: (166, 24, 93),
    3: (13, 4, 72), # Cord
    4: (204, 153, 51),

}

def generate_entropy_map(logits: torch.Tensor, normalize: bool = True, image=None):

    # Convert logits to probabilities
    probs = F.softmax(logits, dim=1)

    # Compute entropy
    entropy = -(probs * torch.log(probs + 1e-8)).sum(dim=1)

    if normalize:
        num_classes = logits.shape[1]
        entropy = entropy / torch.log(torch.tensor(num_classes, device=logits.device).float())

    plt.figure(figsize=(6,6))
    plt.imshow(img)
    plt.imshow(entropy[0], cmap="magma", alpha=0.35)
    plt.axis("off")
    plt.title("Model Uncertainty")
    plt.colorbar()
    plt.savefig("uncertainty", dpi=300, bbox_inches="tight")
    plt.close()

# Contour code

def generate_contours(pred_mask):
    mask = pred_mask.cpu().numpy().astype(np.uint8)

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    return contours

def draw_multiclass_contours(logits, overlay, class_colors=None, thickness=2):

    pred_mask = torch.argmax(logits, dim=1)[0]
    num_classes = logits.shape[1]

    if class_colors is None:
        np.random.seed(42)
        class_colors = [tuple(np.random.randint(0,256,3).tolist()) for _ in range(num_classes)]

    for class_id in range(num_classes):

        binary_mask = (pred_mask == class_id).detach().cpu().numpy().astype(np.uint8) * 255

        if binary_mask.sum() == 0:
            continue

        contours, hierarchy = cv2.findContours(
            binary_mask,
            cv2.RETR_TREE,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if hierarchy is None:
            continue

        for i, contour in enumerate(contours):

            outer_color = class_colors[class_id]
            inner_color = tuple(int(v * 0.5) for v in outer_color)

            if hierarchy[0][i][3] == -1:
                cv2.drawContours(overlay, [contour], -1, outer_color, thickness)
            else:
                cv2.drawContours(overlay, [contour], -1, inner_color, thickness)

    cv2.imwrite("contours.png", overlay)

def calculate_confidence_score(logits):
    probs = F.softmax(logits, dim=1)
    confidence_score = probs.max(dim=1)[0].mean().item()
    return confidence_score
    
def mask_to_rgb(mask, color_map):
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for cls, color in color_map.items():
        rgb[mask == cls] = color
    return rgb

def generate_prediction_overlay(preds):
    # Converts the model output to a 2d Numpy Array Mask
    mask = preds.squeeze(0).cpu().numpy()
    h, w = mask.shape
    # Create the mask with RGBA channels
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Create a semi-transparent overlay based on the predicted classes
    for cls_id, (r, g, b) in cls_to_rgb.items():
        if cls_id == 0:  # background
            continue

        rgba[mask == cls_id] = [r, g, b, 140]


    img = Image.fromarray(rgba, mode="RGBA")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    img.save("prediction_overlay.png")

    return buffer

def generate_entropy_overlay(logits, normalize: bool = True, alpha: float = 0.45,
):
    probs = F.softmax(logits, dim=1)
    entropy = -(probs * torch.log(probs + 1e-8)).sum(dim=1)

    if normalize:
        num_classes = logits.shape[1]
        entropy = entropy / torch.log(
            torch.tensor(num_classes, device=logits.device).float()
        )

    entropy_np = entropy[0].detach().cpu().numpy()
    entropy_np = np.clip(entropy_np, 0.0, 1.0)

    colored = cm.get_cmap("magma")(entropy_np)  # H x W x 4, floats in [0,1]
    colored[..., 3] = entropy_np * alpha        # use entropy as transparency

    rgba = (colored * 255).astype(np.uint8)
    img = Image.fromarray(rgba, mode="RGBA")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer

def run_model(img):
    model = make_model()
    model.load_state_dict(torch.load("unet_resnet34.pth"))
    model.eval()

    transform = T.Compose([
        T.ToTensor(),
    ])

    x = transform(img).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        preds = torch.argmax(logits, dim=1)
    
    return logits, preds

def post_process(preds):
    results = []
    # Convert to binary mask for the cord class(3)
    cord_mask = (preds == 3).astype(np.uint8)
    num_cords, cord_labels = cv2.connectedComponents(cord_mask)

    # For each cord instance, extract its mask
    for cord_id in range(1, num_cords):
        single_cord = (cord_labels == cord_id)
        
        # For the cord mask find the artery mask and vein mask within
        artery_mask = ((preds == 1) & single_cord).astype(np.uint8)
        vein_mask   = ((preds == 2) & single_cord).astype(np.uint8)

        # Run connected components again to get instances
        num_arteries, artery_labels = cv2.connectedComponents(artery_mask)
        num_veins, vein_labels    = cv2.connectedComponents(vein_mask)

        results.append({
            "cord_id": cord_id,
            "cord_mask": single_cord,
            "num_arteries": num_arteries - 1, # subtract 1 for background
            "num_veins": num_veins - 1,
            "artery_labels": artery_labels[artery_labels > 0],
            "vein_labels": vein_labels[vein_labels > 0]
        })

    return results

def predict_SUA(num_arteries, num_veins):
    if num_arteries == 1 and num_veins == 1:
        return "SUA"
    elif num_arteries == 2 and num_veins == 1:
        return "Normal"
    else: 
        return "Uncertain"



# Load image
img = Image.open("../dataset/images/case232.jpg").convert("RGB")
image_np = np.array(img) 

# Copy to draw contours
overlay = image_np.copy()

logits, preds = run_model(img)

generate_prediction_overlay(preds)

generate_entropy_map(logits, True, img)

# Generate the entropy confidence map
# generate_entropy_map(logits, True, img)

# Generate the colored segmentation mask
# mask = preds.squeeze(0).cpu().numpy()
# rgb_mask = mask_to_rgb(mask, cls_to_rgb)
# Image.fromarray(rgb_mask).save("prediction.png")

# Generate contour map
contour_map = draw_multiclass_contours(logits, overlay)
