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
from torchmetrics.classification import (
    MulticlassJaccardIndex,
    MulticlassF1Score,
)
import torch.nn.functional as F
import matplotlib.pyplot as plt

PATIENCE = 10
#–--- Instantiate the Dataset ------------------------------------------------

# Make lists of corresponding image and mask paths
img_dir = "../dataset/images"
mask_dir = "../dataset/masks"

img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".jpg")])

img_paths, mask_paths = [], []
for f in img_files:
    case_number = os.path.splitext(f)[0]
    mask_paths = os.path.join(mask_dir, case_number + ".png")
    if os.path.exists(mask_paths):
        img_paths.append(os.path.join(img_dir, f))
        mask_paths.append(mask_paths)
    else:
        print("Missing mask for:", f)

dataset = FickDataSet(
    img_paths=img_paths,
    mask_paths=mask_paths,
    img_tf=ToTensor(),   # simple for now
)


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {device} device")

class_names = ["Background","Artery","Vein","Vessel", "Roll"]

# -- Hyperparamters  ----------------------------------------------------------------
learning_rate = 1e-4
batch_size = 5
epochs = 70

# -- Loss Function ----------------------------------------------------------------

loss_fn = torch.nn.CrossEntropyLoss(ignore_index=255)

# -- Evaluation Metrics  ----------------------------------------------------------------
iou_metric       = MulticlassJaccardIndex(num_classes=5, average="none", ignore_index=255).to(device)
dice_metric      = MulticlassF1Score(num_classes=5, average="none", ignore_index=255).to(device)

# --- History for plotting ---
train_losses = []
val_losses   = []

# -- Training ----------------------------------------------------------------------------

def train_loop(train_dataloader, model, optimizer):
    model.train()
    running_loss = 0.0

    for batch, (X, y) in enumerate(train_dataloader):
        optimizer.zero_grad()

        X = X.to(device)
        y = y.to(device)

        if y.ndim == 4:
            y = torch.argmax(y, dim=1)
        y = y.long()

        pred = model(X)
        loss = loss_fn(pred, y)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    return running_loss / len(train_dataloader)

# Testing / Validation ----------------------------------------------------------------------------
def test_loop(test_dataloader, model):
    model.eval()
    iou_metric.reset()
    dice_metric.reset()
    running_loss = 0.0

    with torch.no_grad():
        for X, y in test_dataloader:
            X = X.to(device)
            y = y.to(device)

            if y.ndim == 4:
                y = torch.argmax(y, dim=1)
            y = y.long()

            logits = model(X)   
            preds = torch.argmax(logits, dim=1)

            loss = loss_fn(logits, y)
            running_loss += loss.item()

            ## Update metrics
            iou_metric.update(preds, y)
            dice_metric.update(preds, y)

    miou      = iou_metric.compute()
    mdice     = dice_metric.compute()
    mean_loss = running_loss / len(test_dataloader)
    mean_iou  = miou.mean()
    mean_dice = mdice.mean()

    print(f"\n{'Class':<12} {'Dice':>8} {'IoU':>8}")
    print("-" * 30)
    for i, name in enumerate(class_names):
        print(f"{name:<12} {mdice[i]:>8.4f} {miou[i]:>8.4f}")
    print("-" * 30)
    print(f"{'Mean':<12} {mean_dice:>8.4f} {mean_iou:>8.4f}")
    print(f"Loss: {mean_loss:.4f}")

    return mean_loss, mean_dice.item(), mean_iou.item()


def plot_training_curves():
    epochs_range = range(1, len(train_losses) + 1)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    axes[0].plot(epochs_range, train_losses, label="Train Loss")
    axes[0].plot(epochs_range, val_losses, label="Val Loss")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()

    plt.tight_layout()
    plt.savefig("training_curves.png", dpi=150)
    plt.show()
    print("Saved training_curves.png")


# -- Training Validation Test Split ---------------------------------------------------------------------------
n = len(dataset)
n_train = int(0.7 * n)
n_val = int(0.15 * n)
n_test = n - n_train - n_val

train_set, val_set, test_set = random_split(dataset, [n_train, n_val, n_test])

# -- Creating Dataloader ---------------------------------------------------------------------------
train_dataloader = DataLoader(train_set, batch_size=batch_size, shuffle=True)
val_dataloader = DataLoader(val_set, batch_size=batch_size, shuffle=False)
test_dataloader = DataLoader(test_set, batch_size=batch_size, shuffle=False)

# Initialise an instance of the model
model = make_model().to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

best_val_dice = 0.0
best_model_state = None

# Training ---------------------------------------------------------------
epochs_without_improvement = 0
for t in range(epochs):
    print(f"Epoch {t+1}\n-------------------------------")

    train_loss = train_loop(train_dataloader, model, optimizer)
    print("Training results")
    print("Mean Loss:", train_loss)

    print("\nValidation results")
    val_loss, val_dice, val_iou = test_loop(val_dataloader, model)

    if val_dice > best_val_dice:
        best_val_dice = val_dice
        best_model_state = model.state_dict().copy()
        epochs_without_improvement = 0
    else:
        epochs_without_improvement += 1
        if epochs_without_improvement >= PATIENCE:
            print(f"\nEarly stopping triggered after {t+1} epochs.")
            break
    
    train_losses.append(train_loss)
    val_losses.append(val_loss)

# --- Final evaluation on test set -----------------------------
model.load_state_dict(best_model_state)

print("\nFinal Test Results")
print("==============================")

test_loss, test_dice, test_iou = test_loop(test_dataloader, model)

plot_training_curves()
# Save the model state for prediction
torch.save(model.state_dict(), "unet_resnet34_v1.pth")

print("Done!")