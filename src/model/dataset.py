import os
from torch.utils.data import Dataset
import numpy as np
import torch
from PIL import Image


# Required transformation for the image transform *todo*

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
        mask = Image.open(self.mask_paths[idx])

        if self.img_tf:
            img = self.img_tf(img)

        mask = torch.from_numpy(np.array(mask))

        return img, mask


