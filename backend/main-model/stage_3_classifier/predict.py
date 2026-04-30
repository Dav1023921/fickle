import os
import joblib
import numpy as np
from xgboost import XGBClassifier

model = XGBClassifier()
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xgboost_classifier.json")
model.load_model(model_path)

scaler_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "morphology_scaler.pkl")
scaler = joblib.load(scaler_path)

def predict_artery_vein(feature_vector, threshold=0.6):
    feature_vector = feature_vector.copy()
    feature_vector[:, 512:] = scaler.transform(feature_vector[:, 512:])

    label = model.predict(feature_vector)[0]
    probability = model.predict_proba(feature_vector)
    print("raw label:", label)
    print("raw probability:", probability)

    artery_prob = float(probability[0][1])
    vein_prob = float(probability[0][0])

    if artery_prob >= threshold:
        return "Artery", artery_prob
    elif vein_prob >= threshold:
        return "Vein", vein_prob
    else:
        confidence = max(artery_prob, vein_prob)
        return "Uncertain", confidence