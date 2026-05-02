import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    roc_auc_score
)
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

# AUC-ROC
auc = roc_auc_score(y_test, y_prob[:, 1])
print(f"AUC-ROC: {auc:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Vein", "Artery"]))

# Confusion matrix with specificity and sensitivity
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(cm)

tn, fp, fn, tp = cm.ravel()
sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
print(f"\nSensitivity (Recall for Artery): {sensitivity:.4f}")
print(f"Specificity (Recall for Vein):   {specificity:.4f}")

# Cross-validation on full dataset (scaled morphology features only)
print("\n--- Cross-Validation (5-fold, AUC-ROC) ---")
features_cv = features.copy()
cv_scaler = StandardScaler()
features_cv[:, 512:] = cv_scaler.fit_transform(features_cv[:, 512:])

cv_model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="logloss",
    random_state=42,
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(cv_model, features_cv, labels, cv=skf, scoring="roc_auc")
print(f"Cross-val AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
print(f"Per-fold AUC:  {[round(s, 4) for s in cv_scores]}")

# Feature importance
print("\n--- Feature Importance ---")
importances = model.feature_importances_
print(f"CNN features importance (sum): {importances[:512].sum():.4f}")
print(f"Morphology features importance (sum): {importances[512:].sum():.4f}")
print("Morphology breakdown:")
morph_names = ["relative_area", "relative_perimeter", "circularity", "aspect_ratio", "total_vessels"]
for name, imp in zip(morph_names, importances[512:]):
    print(f"  {name}: {imp:.4f}")

# Save model
model.save_model("xgboost_classifier.json")
print("\nModel saved to xgboost_classifier.json")