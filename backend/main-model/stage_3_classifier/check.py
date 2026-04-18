import numpy as np
import joblib
from xgboost import XGBClassifier

features = np.load("classifier-dataset/features.npy")
labels = np.load("classifier-dataset/labels.npy")

model = XGBClassifier()
model.load_model("xgboost_classifier.json")
scaler = joblib.load("morphology_scaler.pkl")

features[:, 512:] = scaler.transform(features[:, 512:])
preds = model.predict(features)
print("Unique predictions:", np.unique(preds, return_counts=True))