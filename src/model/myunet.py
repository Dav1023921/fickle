import segmentation_models_pytorch as smp
import torch


def make_model():
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=3,
        classes=4,
    )
    return model


