import os
from torch.utils.data import Dataset
import numpy as np
import torch
from PIL import Image
import torch.nn.functional as F

# Required transformation for the image transform *todo*

def pad_to_1024(x, fill=0):
    h, w = x.shape[-2], x.shape[-1]

    pad_h = 1024 - h
    pad_w = 1024 - w

    if pad_h < 0 or pad_w < 0:
        raise ValueError(f"Image size ({h}, {w}) larger than 1024")

    # (left, right, top, bottom)
    return F.pad(x, (0, pad_w, 0, pad_h), value=fill)

color_map = {
    (0, 0, 0): 0, # Background
    (56,37,158): 1, # Artery 
    (166,24,93): 2 # Vein
}




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
        img = Image.open(self.img_paths[idx]).convert("RGB")

        mask_rgb = Image.open(self.mask_paths[idx]).convert("RGB")
        mask_rgb = np.array(mask_rgb, dtype=np.uint8)
        mask = rgb_to_mask(mask_rgb, color_map)
        mask = torch.from_numpy(mask).long()

        if self.img_tf:
            img = self.img_tf(img)

        img = pad_to_1024(img, fill=0)
        mask = pad_to_1024(mask, fill=255)  # important for CE loss

        return img, mask

