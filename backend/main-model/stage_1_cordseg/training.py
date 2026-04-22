import copy
import segmentation_models_pytorch as smp
import torch
from torch.utils.data import DataLoader
from torchvision.transforms import ToTensor
from myunet import make_model
from dataset import FickDataSet
import os
from torch.utils.data import random_split
from torchmetrics.classification import MulticlassJaccardIndex, MulticlassF1Score
from PIL import Image
import numpy as np
from dataset import FickDataSet, AugmentedSubset


## paths to the image files #########

img_dir  = "cord-dataset/images"
mask_dir = "cord-dataset/masks"

## extracting file names to create a dataset ########

img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".jpg")])

img_paths, mask_paths = [], []
for f in img_files:
    case_no = os.path.splitext(f)[0]
    mask_path = os.path.join(mask_dir, case_no + ".png")
    if os.path.exists(mask_path):
        img_paths.append(os.path.join(img_dir, f))
        mask_paths.append(mask_path)
    else:
        print("Missing mask for:", f)

# Stain Normalisation
REFERENCE_IMAGE = img_paths[0] 
reference = np.array(Image.open(REFERENCE_IMAGE).convert("RGB"))

# Create the dataset
dataset = FickDataSet(
    img_paths=img_paths,
    mask_paths=mask_paths,
    img_tf=ToTensor(),
    reference=reference
)

# Move to gpu
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {device} device")

class_names = ["Background", "Vessel"]

# Hyperparameters 
learning_rate = 1e-4
batch_size = 5
epochs = 40

# Loss Function - uses a combination of cross-entropy and soft Dice loss
# ignore_index=255 ignores values of 255 in the mask
_ce_loss   = torch.nn.CrossEntropyLoss(ignore_index=255)
_dice_loss = smp.losses.DiceLoss(
    mode="multiclass",
    classes=None,       # all classes
    from_logits=True,   # our model outputs raw logits
    ignore_index=255,
)
def combined_loss(logits, targets):
    """Equal-weight sum of cross-entropy and soft Dice loss."""
    return 0.5 * _ce_loss(logits, targets) + 0.5 * _dice_loss(logits, targets)

# Evaluation metrics 
iou_metric  = MulticlassJaccardIndex(num_classes=2, average="none", ignore_index=255).to(device)
dice_metric = MulticlassF1Score(num_classes=2, average="none", ignore_index=255).to(device)

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

        pred = model(X)
        
        loss = combined_loss(pred, y)
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
            y = y.long()

            logits = model(X)   
            preds = torch.argmax(logits, dim=1)

            running_loss += combined_loss(logits, y).item()
            # accumulate metrics
            iou_metric.update(preds, y)
            dice_metric.update(preds, y)
    # compute average over batches
    miou = iou_metric.compute()
    mdice = dice_metric.compute()
    # loss over the whole test dataset
    mean_loss = running_loss / len(test_dataloader)

    for i, name in enumerate(class_names):
        print(f"{name}: Dice={mdice[i]:.4f}, IoU={miou[i]:.4f}")
    print("Mean Loss:", mean_loss)

    return mean_loss, mdice

# ----------------------------------------------------------

# Split into train / validation / test 
n = len(dataset)
n_train, n_val, n_test = int(0.7 * n), int(0.15 * n), int(0.15 * n)

train_set, val_set, test_set = random_split(dataset, [n_train, n_val, n_test])

train_set = AugmentedSubset(train_set)

# Creating Dataloader
train_dataloader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
val_dataloader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
test_dataloader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

# Initialise an instance of the model
model = make_model().to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

# Track best val_dice and model state
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
    print("Validation Loss:", val_loss)
    vessel_dice = val_dice[1].item()   # Vessel class only
    if vessel_dice > best_val_dice:
        best_val_dice    = vessel_dice
        best_model_state = copy.deepcopy(model.state_dict())

# Load best model before final test
model.load_state_dict(best_model_state)

print("\nFinal test results")
print("-------------------------------")
test_loop(test_dataloader, model)

# Save the model state for prediction
torch.save(model.state_dict(), "unet_resnet34.pth")

print("Done!")