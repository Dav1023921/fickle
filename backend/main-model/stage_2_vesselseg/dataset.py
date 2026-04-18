import os
from torch.utils.data import Dataset
import numpy as np
import torch
from PIL import Image
import torch.nn.functional as F
from torchvision.transforms import RandomCrop
from torchvision.transforms import functional as F


color_map = {
    (0, 0, 0): 0, # Background
    (255,53,94) : 1, # Artery
    (53,21,212) : 1, # Vein
    (10, 10, 10): 0, # Ignore
}

# def pad_to_512(img, width, height, fill):
#     pad_w = max(0, 512 - width)
#     pad_h = max(0, 512 - height)
#     # pad the image
#     img = F.pad(img, (0, 0, pad_w, pad_h), fill=fill)
#     return img

def rgb_to_mask(mask_rgb, color_map):
    h, w, _ = mask_rgb.shape

    mask = np.zeros((h, w), dtype=np.int64)

    for color, class_id in color_map.items():
        matches = np.all(mask_rgb == np.array(color, dtype=np.uint8), axis=-1)
        mask[matches] = class_id

    return mask

class FickDataSet(Dataset):
    def __init__(self, img_paths, mask_paths, img_tf=None, mask_tf=None):
        self.img_paths = img_paths
        self.mask_paths = mask_paths
        self.img_tf = img_tf
        self.mask_tf = mask_tf

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        # patching dimensions
        dim = 512

        # Converting images into RGB
        img = Image.open(self.img_paths[idx]).convert("RGB")
        mask_rgb = Image.open(self.mask_paths[idx]).convert("RGB")
        # Pad if necessary
        # width, height = img.size
        # img = pad_to_512(img, width, height, 0)
        # mask_rgb = pad_to_512(mask_rgb,width, height, (10,10,10))

        # Converting an RGB mask to segmentation Mask
        mask_rgb = np.array(mask_rgb, dtype=np.uint8)
        mask = rgb_to_mask(mask_rgb, color_map)
        mask = torch.from_numpy(mask).long()

        if self.img_tf:
            img = self.img_tf(img)

        return img, mask

