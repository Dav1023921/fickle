from PIL import Image
import torchvision.transforms as T
import torch
from myunet import make_model
import numpy as np
from dataset import color_map
from dataset import pad_to_1024



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
img = Image.open("../dataset/images/case59.jpg").convert("RGB")

transform = T.Compose([
    T.ToTensor(),
])

x = transform(img).unsqueeze(0)   # (1, 3, H, W)
# x = pad_to_1024(x, fill=0)        # only if pad_to_1024 expects a tensor with .shape

with torch.no_grad():
    logits = model(x)
    preds = torch.argmax(logits, dim=1)  # (1,H,W)

mask = preds.squeeze(0).cpu().numpy()

rgb_mask = mask_to_rgb(mask, cls_to_rgb)
Image.fromarray(rgb_mask).save("prediction.png")