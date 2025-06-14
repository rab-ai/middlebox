#!/usr/bin/env python3
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, classification_report
)
import warnings
warnings.filterwarnings("ignore")

print("=== REAL PACKET DETECTION PERFORMANCE ===\n")

# 1) Load the test set
print("Loading data...")
df = pd.read_csv("test_features.csv")
print(f"Total number of packets: {len(df)}")

# 2) Remove outliers (drop if inter-arrival > 2 sec)
df = df[df["inter_arrival"] < 2].reset_index(drop=True)
print(f"After outlier removal: {len(df)}")

# 3) Select features and labels
feature_cols = ["length", "inter_arrival", "entropy"]
X = df[feature_cols]
y = df["label"].map({"normal": 0, "covert": 1})

print(f"Final dataset size: {len(X)}")
print("Class distribution:")
print(y.value_counts())
print("Class proportions:")
print(y.value_counts(normalize=True))

# 4) Load the model
print("\nLoading model...")
clf = joblib.load("detector_model_entropy.pkl")
print("✓ Model loaded successfully")

# 5) Prediction & basic metrics
print("\n=== OVERALL PERFORMANCE ===")
y_pred = clf.predict(X)
y_pred = pd.Series(y_pred).map({"normal": 0, "covert": 1})
tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()

acc  = accuracy_score(y, y_pred)
prec = precision_score(y, y_pred, zero_division=0)
rec  = recall_score(y, y_pred, zero_division=0)
f1   = f1_score(y, y_pred, zero_division=0)

print("Confusion Matrix:")
print(f"              Predicted")
print(f"           0      1")
print(f"Actual 0  {tn:4d}  {fp:4d}")
print(f"       1  {fn:4d}  {tp:4d}\n")

print(f"TP={tp}  TN={tn}  FP={fp}  FN={fn}")
print(f"Accuracy={acc:.4f}  Precision={prec:.4f}  Recall={rec:.4f}  F1={f1:.4f}")

print("\nDetailed classification report:")
print(classification_report(y, y_pred, zero_division=0))

# 6) Bootstrap 95% Confidence Interval
print("\n=== BOOTSTRAP ANALYSIS (95% Confidence Interval) ===")
n_iter = 1000
rng = np.random.default_rng(42)
metrics = {"accuracy":[], "precision":[], "recall":[], "f1":[], "tp":[], "tn":[], "fp":[], "fn":[]}

for _ in range(n_iter):
    idx = rng.choice(len(y), size=len(y), replace=True)
    y_b = y.iloc[idx].reset_index(drop=True)
    X_b = X.iloc[idx].reset_index(drop=True)
    y_pred_b = clf.predict(X_b)
    y_pred_b = pd.Series(y_pred_b).map({"normal": 0, "covert": 1})
    tn_b, fp_b, fn_b, tp_b = confusion_matrix(y_b, y_pred_b, labels=[0,1]).ravel()
    metrics["accuracy"].append(accuracy_score(y_b, y_pred_b))
    metrics["precision"].append(precision_score(y_b, y_pred_b, zero_division=0))
    metrics["recall"].append(recall_score(y_b, y_pred_b, zero_division=0))
    metrics["f1"].append(f1_score(y_b, y_pred_b, zero_division=0))
    metrics["tp"].append(tp_b)
    metrics["tn"].append(tn_b)
    metrics["fp"].append(fp_b)
    metrics["fn"].append(fn_b)

print(f"{'Metric':<15} {'Average':<8} {'95% CI':<20}")
for m in ["accuracy", "precision", "recall", "f1", "tp", "tn", "fp", "fn"]:
    arr = np.array(metrics[m])
    lo, hi = np.percentile(arr, [2.5, 97.5])
    print(f"{m:<15} {arr.mean():.4f}   [{lo:.4f} – {hi:.4f}]")
