import torch
import torchvision.models as models
import torchvision.transforms as T
import numpy as np
import torchvision.models as models

############## CNN FEATURE MODEL ##########################################
# Load pretrained ResNet34 and remove the final classification layer
def load_feature_extractor():
    resnet = models.resnet34(weights=models.ResNet34_Weights.DEFAULT)
    feature_extractor = torch.nn.Sequential(*list(resnet.children())[:-1])
    feature_extractor.eval()
    for param in feature_extractor.parameters():
        param.requires_grad = False
    return feature_extractor

# Transform for ResNet input
resnet_transform = T.Compose([
    T.ToPILImage(),
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225])
])

####################################################################################

### Gets the CNN features
def extract_cnn_features(crop, feature_extractor):
    ### Takes a crop and transforms it
    x = resnet_transform(crop).unsqueeze(0)
    ### Passes through the feature extractor to get a 512-dim vector
    with torch.no_grad():
        features = feature_extractor(x)
        features = features.squeeze()
    return features.numpy()

### Gets the morphology features
def get_morphology_vector(instance):
    """
    Extract morphology features from an instance dict
    into a numpy vector ready to concatenate with CNN features
    """
    return np.array([
        instance["relative_perimeter"],
        instance["relative_circularity"],
        instance["relative_aspect_ratio"],
        instance["relative_area"],
        instance["num_vessels"]
    ], dtype=np.float32)

    

def get_combined_features(instance):
    feature_extractor = load_feature_extractor()
    """
    Full pipeline: crop + instance dict → 520-dim feature vector
    """
    cnn_features = extract_cnn_features(instance["crop"], feature_extractor)
    morphology = get_morphology_vector(instance)
    return np.concatenate([cnn_features, morphology])