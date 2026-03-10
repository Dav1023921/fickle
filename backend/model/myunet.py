import segmentation_models_pytorch as smp

# define a cnn model with a resnet34 pretrained encoder and a Unet architecture

def make_model():
    model = smp.Unet(
        encoder_name="resnet34",
        encoder_weights="imagenet",
        in_channels=3,
        classes=4,
    )
    return model


