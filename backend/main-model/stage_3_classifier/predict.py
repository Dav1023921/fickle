import os
import joblib
import numpy as np
from xgboost import XGBClassifier

model = XGBClassifier()
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xgboost_classifier.json")
model.load_model(model_path)

scaler_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "morphology_scaler.pkl")
scaler = joblib.load(scaler_path)

def predict_artery_vein(feature_vector):
    feature_vector = feature_vector.copy()
    feature_vector[:, 512:] = scaler.transform(feature_vector[:, 512:])
    
    vessel_type = None
    label = model.predict(feature_vector)[0]
    probability = model.predict_proba(feature_vector)
    print("raw label:", label)
    print("raw probability:", probability)
    if label == 1:
        vessel_type = "Artery"
        confidence = float(probability[0][1])
    else: 
        vessel_type = "Vein"
        confidence = float(probability[0][0]) 

    return vessel_type, confidence

