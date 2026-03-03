import numpy as np
from PIL import Image

mask = np.array(Image.open("../dataset/masks/case0.png"))
print(np.unique(mask))