from torch.utils.data import Dataset
import numpy as np
import torch
from PIL import Image
from torchvision.transforms import Normalize, RandomCrop
from torchvision.transforms import functional as F
import cv2
import numpy as np
import random


# The masks are in the form of RGB images when exported by CVAT.
# I encode their RGB values into class labels using this color map.
color_map = {
    (0, 0, 0): 0, # Background
    (13, 4, 72): 1, # Vessel
    (10, 10, 10): 255, # Ignore
}

# This uses ImageNet normalization, which is needed for the pretrained ResNet34 encoder,
# I found that it converged faster with this normalization.
imagenet_normalize = Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])


def pad_to_512(img, width, height, fill):
    pad_w = max(0, 512 - width)
    pad_h = max(0, 512 - height)
    # pad the image
    img = F.pad(img, (0, 0, pad_w, pad_h), fill=fill)
    return img

# convert rgb image to mask
def rgb_to_mask(mask_rgb, color_map):
    h, w, _ = mask_rgb.shape

    mask = np.zeros((h, w), dtype=np.int64)

    for color, class_id in color_map.items():
        matches = np.all(mask_rgb == np.array(color, dtype=np.uint8), axis=-1)
        mask[matches] = class_id

    return mask

# data augmentation
def augment(img, mask):
    # Random vertical or horizontal flip
    if random.random() > 0.5:
        flip_no = random.choice([0, 1])  # 0: vertical, 1: horizontal

        if flip_no == 0:
            img  = F.vflip(img)
            mask = F.vflip(mask)
        else:
            img  = F.hflip(img)
            mask = F.hflip(mask)

    # Random 90 degree rotation
    if random.random() > 0.5:
        angle = random.choice([90, 180, 270])
        img  = F.rotate(img, angle)
        mask = F.rotate(mask.unsqueeze(0), angle).squeeze(0)  # add/remove channel dim

    # Colour jitter on image only
    if random.random() > 0.5:
        img = F.adjust_brightness(img, brightness_factor=random.uniform(0.8, 1.2))
        img = F.adjust_contrast(img,   contrast_factor=random.uniform(0.8, 1.2))

    return img, mask

# A wrapper dataset that applies data augmentation specifically for the training data
class AugmentedSubset(Dataset):
    def __init__(self, subset):
        self.subset = subset

    def __len__(self):
        return len(self.subset)

    def __getitem__(self, idx):
        img, mask = self.subset[idx]
        img, mask = augment(img, mask)
        return img, mask

class FickDataSet(Dataset):
    def __init__(self, img_paths, mask_paths, img_tf=None, mask_tf=None,
                 reference=None):
        self.img_paths = img_paths
        self.mask_paths = mask_paths
        self.img_tf = img_tf
        self.mask_tf = mask_tf
        self.reference  = reference

    def __len__(self):
        return len(self.img_paths)

    def __getitem__(self, idx):
        # we use 512 x 512 patches in this training
        dim = 512

        # Converting images into RGB
        img = Image.open(self.img_paths[idx]).convert("RGB")
        mask_rgb = Image.open(self.mask_paths[idx]).convert("RGB")

        # Pad if necessary
        width, height = img.size
        img = pad_to_512(img, width, height, 0)
        mask_rgb = pad_to_512(mask_rgb,width, height, (10,10,10))

        # Converting an RGB mask to segmentation Mask
        mask_rgb = np.array(mask_rgb, dtype=np.uint8)
        mask = rgb_to_mask(mask_rgb, color_map)
        mask = torch.from_numpy(mask).long()

        # Stain normalisation
        if self.reference is not None:
            img_np = np.array(img)  # PIL to numpy
            source_lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB).astype(float)
            target_lab = cv2.cvtColor(self.reference, cv2.COLOR_RGB2LAB).astype(float)
            for i in range(3):
                source_lab[:,:,i] = (source_lab[:,:,i] - source_lab[:,:,i].mean()) \
                                / (source_lab[:,:,i].std() + 1e-6) \
                                * target_lab[:,:,i].std() \
                                + target_lab[:,:,i].mean()
            img_np = cv2.cvtColor(np.clip(source_lab, 0, 255).astype(np.uint8), 
                                cv2.COLOR_LAB2RGB)
            img = Image.fromarray(img_np)


        # Convert to Tensor
        if self.img_tf:
            img = self.img_tf(img)

        # Return a random crop of the image and the corresponding crop of the mask
        i, j, h, w = RandomCrop.get_params(img, output_size=(dim, dim))
        img = F.crop(img, i, j, h, w)
        mask = F.crop(mask, i, j, h, w)

        # Normalization
        img = imagenet_normalize(img)

        return img, mask





