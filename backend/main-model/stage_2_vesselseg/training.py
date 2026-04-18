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
from torchmetrics.classification import MulticlassJaccardIndex, MulticlassF1Score
import torch.nn.functional as F
from torchmetrics.classification import BinaryJaccardIndex, BinaryF1Score


import torch

class EarlyStopping:
    def __init__(self, patience=10, min_delta=0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_dice = 0.0

    def step(self, val_dice):
        if val_dice > self.best_dice + self.min_delta:
            self.best_dice = val_dice
            self.counter = 0
            return False  # don't stop
        else:
            self.counter += 1
            return self.counter >= self.patience  # stop if True
        
print(torch.backends.mps.is_available())

# Training ################################################
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

        pred = model(X)
        y = y.float().unsqueeze(1)
        loss = combined_loss(pred, y)

        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        print(f"Batch {batch+1}/{len(train_dataloader)} processed")

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

            logits = model(X)
            preds = (torch.sigmoid(logits) > 0.5).long().squeeze(1)  # [8, 512, 512]
            y_long = y.long()  # [8, 512, 512] for metrics

            loss = combined_loss(logits, y.float().unsqueeze(1))
            running_loss += loss.item()

            iou_metric.update(preds, y_long)
            dice_metric.update(preds, y_long)
    # compute average over batches
    miou = iou_metric.compute()
    mdice = dice_metric.compute()
    # loss over the whole test dataset
    mean_loss = running_loss / len(test_dataloader)

    print(f"Vessel: Dice={mdice:.4f}, IoU={miou:.4f}")

    return mean_loss, mdice

if __name__ == '__main__':
    ## paths to the image files #########
    img_dir  = "vessel-dataset/images"
    mask_dir = "vessel-dataset/masks"

    ## extracting file names to create a dataset ########

    img_files = sorted([f for f in os.listdir(img_dir) if f.lower().endswith(".png")])

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

    # Move to gpu ####################################
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using {device} device")

    class_names = ["Vessel"]

    # Hyperparameters ##############################################
    learning_rate = 1e-4
    batch_size = 8
    epochs = 50

    # Evaluation metrics #######################################
    # ignore_index=255 ignores values of 255 in the mask
    bce_loss = torch.nn.BCEWithLogitsLoss()
    dice_loss = smp.losses.DiceLoss(mode='binary')

    def combined_loss(pred, target):
        return bce_loss(pred, target) + dice_loss(pred, target)

    iou_metric  = BinaryJaccardIndex().to(device)
    dice_metric = BinaryF1Score().to(device)



    # -----------------------------
    ## Split into train / validation / test #######

    n = len(dataset)
    n_train = int(0.7 * n)
    n_val = int(0.15 * n)
    n_test = n - n_train - n_val

    train_set, val_set, test_set = random_split(dataset, [n_train, n_val, n_test])

    # Creating Dataloader
    train_dataloader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers = 3)
    val_dataloader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers = 3)
    test_dataloader = DataLoader(test_set, batch_size=batch_size, shuffle=False, num_workers = 3)

    # Initialise an instance of the model
    model = make_model().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    best_val_dice = 0.0
    best_model_state = None

    early_stopping = EarlyStopping(patience=10, min_delta=0.001)
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

        if early_stopping.step(val_dice):
            print(f"Early stopping at epoch {t+1}")
            break

    # Load best model before final test
    model.load_state_dict(best_model_state)

    print("\nFinal test results")
    print("-------------------------------")
    test_loop(test_dataloader, model)

    # Save the model state for prediction
    torch.save(model.state_dict(), "unet_resnet34.pth")

    print("Done!")


