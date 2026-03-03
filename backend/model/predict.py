from PIL import Image
import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
from dataset import color_map
from dataset import pad_to_1024



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
img = Image.open("test_image.jpg").convert("RGB")
pad_to_1024(img, fill=0)


# Apply SAME transforms used in training (except augmentations)
transform = T.Compose([
    T.ToTensor(),
])

x = transform(img).unsqueeze(0)  # (1,3,H,W)

with torch.no_grad():
    logits = model(x)
    preds = torch.argmax(logits, dim=1)  # (1,H,W)

mask = preds.squeeze(0).cpu().numpy()

rgb_mask = mask_to_rgb(mask, color_map)
Image.fromarray(rgb_mask).save("prediction.png")