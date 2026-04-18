import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# Load the saved features and labels
features = np.load("classifier-dataset/features.npy")
labels = np.load("classifier-dataset/labels.npy")

# Print data information
print(f"Total samples: {len(labels)}")
print(f"Artery samples (1): {np.sum(labels == 1)}")
print(f"Vein samples (0): {np.sum(labels == 0)}")

# Split into train and test
X_train, X_test, y_train, y_test = train_test_split(
    features, labels,
    test_size=0.2,
    random_state=42,
    stratify=labels  # ensures equal artery/vein split in both sets
)

# Normalise morphology features (last 5 columns)
# CNN features (first 512) are already normalised by ImageNet normalisation
scaler = StandardScaler()
X_train[:, 512:] = scaler.fit_transform(X_train[:, 512:])
X_test[:, 512:] = scaler.transform(X_test[:, 512:])

# Save scaler for inference
joblib.dump(scaler, "morphology_scaler.pkl")

# Train XGBoost
model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
    )


model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=True
)

# Evaluate
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)

print("\n--- Results ---")
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Vein", "Artery"]))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Feature importance
print("\n--- Feature Importance ---")
importances = model.feature_importances_
print(f"CNN features importance (sum): {importances[:512].sum():.4f}")
print(f"Morphology features importance (sum): {importances[512:].sum():.4f}")
print(f"Morphology breakdown:")
morph_names = ["relative_area", "relative_perimeter", "relative_circularity", "relative_aspect_ratio", "total_vessels"]
for name, imp in zip(morph_names, importances[512:]):
    print(f"  {name}: {imp:.4f}")

# Save model
model.save_model("xgboost_classifier.json")
print("\nModel saved to xgboost_classifier.json")