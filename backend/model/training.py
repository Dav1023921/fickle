import segmentation_models_pytorch as smp
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets
from torchvision.transforms import ToTensor
from myunet import make_model
from dataset import FickDataSet
import os
from torch.utils.data import random_split
from torchmetrics.classification import MulticlassJaccardIndex, MulticlassF1Score

# This code here still needs a lot of modification

# Instantiate the Dataset

# Make lists of corresponding image and mask paths
img_dir = "../dataset/images"
mask_dir = "../dataset/masks"

img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".jpg")])

img_paths, mask_paths = [], []
for f in img_files:
    stem = os.path.splitext(f)[0]          
    mp = os.path.join(mask_dir, stem + ".png")
    if os.path.exists(mp):
        img_paths.append(os.path.join(img_dir, f))
        mask_paths.append(mp)
    else:
        print("Missing mask for:", f)

# create a dataset 
dataset = FickDataSet(
    img_paths=img_paths,
    mask_paths=mask_paths,
    img_tf=ToTensor(),   # simple for now
)

n = len(dataset)
n_train = int(0.8 * n)
n_test = n - n_train
train_set, test_set = random_split(dataset, [n_train, n_test])

# Move to gpu
device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
print(f"Using {device} device")

# Initialise an instance of the model
model = make_model()

model = model.to(device)


# Hyperparameters
learning_rate = 1e-3
batch_size = 5
epochs = 5
# Loss function and optimizer
loss_fn = torch.nn.CrossEntropyLoss(ignore_index=255)
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

# Creating Dataloader
train_dataloader = DataLoader(train_set, batch_size=5, shuffle=True)
test_dataloader = DataLoader(test_set, batch_size=5, shuffle=False)

def train_loop(train_dataloader, model, optimizer):
     model.train()

     for batch, (X, y) in enumerate(train_dataloader):
        # Reset gradients for no confliccts
        optimizer.zero_grad()
        # Move data to device
        X = X.to(device)
        y = y.to(device)
        # Compute prediction and loss
        pred = model(X)
        print("Batch processed")
        loss = loss_fn(pred, y)
        # Backpropagation
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    
num_classes = 3
ignore_index = 255

iou_metric  = MulticlassJaccardIndex(num_classes=num_classes, ignore_index=ignore_index)
dice_metric = MulticlassF1Score(num_classes=num_classes, average="macro", ignore_index=ignore_index)


def test_loop(test_dataloader, model):
    iou_metric.reset()
    dice_metric.reset()

    with torch.no_grad():
        for X, y in test_dataloader:
            X = X.to(device)
            y = y.to(device)
            logits = model(X)   
            preds = torch.argmax(logits, dim=1)
            iou_metric.update(preds, y)
            dice_metric.update(preds, y)

    miou = iou_metric.compute().item()
    mdice = dice_metric.compute().item()
    print(f"mIoU: {miou:.4f} | mDice: {mdice:.4f}")


for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")
    train_loop(train_dataloader, model, optimizer)
    test_loop(test_dataloader, model)

torch.save(model.state_dict(), "unet_resnet34.pth")

print("Done!")