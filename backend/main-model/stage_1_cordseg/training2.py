import copy

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
from torchmetrics.classification import BinaryJaccardIndex, BinaryF1Score

import torch.nn.functional as F

## paths to the image files #########

img_dir  = "cord-dataset/images"
mask_dir = "cord-dataset/masks"

## extracting file names to create a dataset ########

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

dataset = FickDataSet(
    img_paths=img_paths,
    mask_paths=mask_paths,
    img_tf=ToTensor(),   
)

# Move to gpu
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {device} device")

class_names = ["Background", "Vessel"]

# Hyperparameters ##########
learning_rate = 1e-4
batch_size = 5
epochs = 40

# Evaluation metrics ##########
# ignore_index=255 ignores values of 255 in the mask

# this class is a custom class that combines BCE and Dice loss 
class BCEDiceLoss(nn.Module):
    def __init__(self, bce_weight=0.5, dice_weight=0.5):
        super().__init__()
        self.bce_weight = bce_weight
        self.dice_weight = dice_weight
        self.bce = nn.BCEWithLogitsLoss()

    def dice_loss(self, logits, targets, smooth=1e-6):
        probs = torch.sigmoid(logits)
        intersection = (probs * targets).sum(dim=(1,2))
        dice = (2 * intersection + smooth) / (probs.sum(dim=(1,2)) + targets.sum(dim=(1,2)) + smooth)
        return 1 - dice.mean()

    def forward(self, logits, targets):
        return self.bce_weight * self.bce(logits, targets) + \
               self.dice_weight * self.dice_loss(logits, targets)


loss_fn = BCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
iou_metric  = BinaryJaccardIndex().to(device)
dice_metric = BinaryF1Score().to(device)

# Training 
def train_loop(train_dataloader, model, optimizer):
    model.train()
    running_loss = 0.0
    # X contains the data and y contains the labels (masks)
    for batch, (X, y) in enumerate(train_dataloader):
        optimizer.zero_grad()

        X = X.to(device)
        y = y.to(device)

        if y.ndim == 4:
            y = torch.argmax(y, dim=1)
        y = y.long()

        pred = model(X).squeeze(1)       
        y = y.float()       
        loss = loss_fn(pred, y)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    return running_loss / len(train_dataloader)

# Testing / Validation
def test_loop(test_dataloader, model):
    model.eval()
    iou_metric.reset()
    dice_metric.reset()
    running_loss = 0.0
    # X contains the data and y contains the labels (masks)
    with torch.no_grad():
        for X, y in test_dataloader:
            X = X.to(device)
            y = y.to(device)

            if y.ndim == 4:
                y = torch.argmax(y, dim=1)
            y = y.float() 
                        
            logits = model(X).squeeze(1)
            preds = (torch.sigmoid(logits) > 0.5).long()

            loss = loss_fn(logits, y)
            running_loss += loss.item()
            # accumulate metrics
            iou_metric.update(preds, y)
            dice_metric.update(preds, y)
    # compute average over batches
    miou = iou_metric.compute()
    mdice = dice_metric.compute()
    # loss over the whole test dataset
    mean_loss = running_loss / len(test_dataloader)

    print(f"Dice={mdice:.4f}, IoU={miou:.4f}")

    return mean_loss

# -----------------------------
## Split into train / validation / test #######

n = len(dataset)
n_train = int(0.7 * n)
n_val = int(0.15 * n)
n_test = n - n_train - n_val

train_set, val_set, test_set = random_split(dataset, [n_train, n_val, n_test])

# Creating Dataloader
train_dataloader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
val_dataloader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
test_dataloader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

# Initialise an instance of the model
model = make_model().to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

best_val_dice = 0.0
best_model_state = None

# Training 
for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")

    train_loss = train_loop(train_dataloader, model, optimizer)
    print("Training results")
    print("Mean Loss:", train_loss)

    print("\nValidation results")
    val_loss, val_dice = test_loop(val_dataloader, model)

    if val_dice > best_val_dice:
        best_val_dice = val_dice
        best_model_state = copy.deepcopy(model.state_dict())

# Load best model before final test
model.load_state_dict(best_model_state)

print("\nFinal test results")
print("-------------------------------")
test_loop(test_dataloader, model)

# Save the model state for prediction
torch.save(model.state_dict(), "unet_resnet34.pth")

print("Done!")


