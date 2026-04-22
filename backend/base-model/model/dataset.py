import os
from torch.utils.data import Dataset
import numpy as np
import torch
from PIL import Image
from torchvision.transforms import Normalize, RandomCrop
from torchvision.transforms import functional as F


# We implement the dataset here, where I use a patch based segmentation training


def pad_to_512(img, width, height, fill):
    pad_w = max(0, 512 - width)
    pad_h = max(0, 512 - height)
    # pad the image
    img = F.pad(img, (0, 0, pad_w, pad_h), fill=fill)
    return img

color_map = {
    (0, 0, 0): 0, # Background
    (56,37,158): 1, # Artery 
    (166,24,93): 2, # Vein
    (13, 4, 72): 3, # Cord
    (204, 153, 51): 4, # Roll 
    (61, 245, 61): 255, # Ignore

}

def rgb_to_mask(mask_rgb, color_map):
    h, w, _ = mask_rgb.shape

    mask = np.zeros((h, w), dtype=np.int64)

    for color, class_id in color_map.items():
        matches = np.all(mask_rgb == np.array(color, dtype=np.uint8), axis=-1)
        mask[matches] = class_id

    return mask

imagenet_normalize = Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

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
        width, height = img.size
        img = pad_to_512(img, width, height, 0)
        mask_rgb = pad_to_512(mask_rgb,width, height, (61,245,61))


        # Converting an RGB mask to segmentation Mask
        mask_rgb = np.array(mask_rgb, dtype=np.uint8)
        mask = rgb_to_mask(mask_rgb, color_map)
        mask = torch.from_numpy(mask).long()

        if self.img_tf:
            img = self.img_tf(img)

        # Return a random crop of the image and the corresponding crop of the mask
        i, j, h, w = RandomCrop.get_params(img, output_size=(dim, dim))
        img = F.crop(img, i, j, h, w)
        mask = F.crop(mask, i, j, h, w)

        img = imagenet_normalize(img)

        return img, mask

