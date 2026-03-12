from PIL import Image
import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
from dataset import color_map
import torch.nn.functional as F
import matplotlib.pyplot as plt
import cv2

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
    
rgb_to_cls = {
    (0, 0, 0): 0,
    (56, 37, 158): 1,
    (166, 24, 93): 2,
    (13, 4, 72): 3,

}
cls_to_rgb = {v: k for k, v in rgb_to_cls.items()}

def mask_to_rgb(mask, color_map):
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for cls, color in color_map.items():
        rgb[mask == cls] = color
    return rgb


model = make_model()
model.load_state_dict(torch.load("unet_resnet34.pth"))
model.eval()


# Load image
img = Image.open("../dataset/images/case232.jpg").convert("RGB")
image_np = np.array(img)  

# Copy to draw contours
overlay = image_np.copy()



transform = T.Compose([
    T.ToTensor(),
])

x = transform(img).unsqueeze(0)   # (1, 3, H, W)
# x = pad_to_1024(x, fill=0)        # only if pad_to_1024 expects a tensor with .shape

with torch.no_grad():
    logits = model(x)
    preds = torch.argmax(logits, dim=1)  # (1,H,W)
    # pred_mask = logits.argmax(dim=1)[0]
    # contours = generate_contours(pred_mask)
    # overlay_image = draw_multiclass_contours(
    # logits,               # [1, C, H, W]
    # img,            # your original image
    # class_colors=[(255,0,0), (0,255,0), (0,0,255)] )
    # # Save to file
    # cv2.imwrite("multiclass_overlay.png", overlay_image)

# Generate the entropy confidence map
generate_entropy_map(logits, True, img)

# Generate the colored segmentation mask
mask = preds.squeeze(0).cpu().numpy()
rgb_mask = mask_to_rgb(mask, cls_to_rgb)
Image.fromarray(rgb_mask).save("prediction.png")

# Generate contour map
contour_map = draw_multiclass_contours(logits, overlay)



# The confidence heatmap
# How to return this
# -》 Entropy map


# The contours polygon (?)
# What format will it export and what does it look like?
# How will it be passed as a function to the confidence score

# Predicted vessel lengths (?)
# Where do we need to look at?
#

# Confidence score (?) : 
# How to calculate the confidence score?
# What other existing proven confidence score methods are there?

# How to make this system in a way that it will be reusable, robust and offer reprediction for editable contours
