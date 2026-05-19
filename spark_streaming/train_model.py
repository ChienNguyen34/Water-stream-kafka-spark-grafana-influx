"""
Phase 3.5 — ML Early Warning: Random Forest Anomaly Detector
Training strategy:
  - Negative class (normal):  BATADAL_dataset03.csv (8761 rows, all normal)
  - Positive class (attacks): BATADAL_synthetic.csv (510 attack rows + 2200 normal)
  - Evaluation: stratified 75/25 split on combined dataset
  - Final model: trained on 100% of combined data

NOTE: dataset04 has ATT_FLAG=-999 (blind test, unlabeled) — not used.

Usage (from project root, with venv activated):
    python spark_streaming/train_model.py
"""

import os
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Features — 31 physical sensor readings, NO time features
# (time is meaningless after COMPRESSION_FACTOR=180000 time-acceleration)
# ---------------------------------------------------------------------------
ML_FEATURES = [
    # Tank levels (7)
    "L_T1", "L_T2", "L_T3", "L_T4", "L_T5", "L_T6", "L_T7",
    # Flow rates — pumps + valve (12)
    "F_PU1", "F_PU2", "F_PU3", "F_PU4", "F_PU5", "F_PU6",
    "F_PU7", "F_PU8", "F_PU9", "F_PU10", "F_PU11", "F_V2",
    # Pump/valve on-off status (12)
    "S_PU1", "S_PU2", "S_PU3", "S_PU4", "S_PU5", "S_PU6",
    "S_PU7", "S_PU8", "S_PU9", "S_PU10", "S_PU11", "S_V2",
]

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "..", "dataset")


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df["ATT_FLAG"] = df["ATT_FLAG"].astype(int)
    # Drop unlabeled rows (dataset04 uses -999 as sentinel)
    return df[df["ATT_FLAG"].isin([0, 1])].reset_index(drop=True)


def main():
    # ------------------------------------------------------------------ data
    ds03 = load_csv(os.path.join(DATASET_DIR, "BATADAL_dataset03.csv"))  # all normal
    syn  = load_csv(os.path.join(DATASET_DIR, "BATADAL_synthetic.csv"))  # normal + attacks
    full = pd.concat([ds03, syn], ignore_index=True)

    n_att  = int((full["ATT_FLAG"] == 1).sum())
    n_norm = int((full["ATT_FLAG"] == 0).sum())
    print(f"Total  : {len(full)} rows | Normal: {n_norm} | Attack: {n_att}")

    X = full[ML_FEATURES].fillna(0.0)
    y = full["ATT_FLAG"]

    # Stratified split preserves class ratio in train/val
    X_tr, X_va, y_tr, y_va = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    print(f"Train  : {len(X_tr)} | Val: {len(X_va)} | Val attacks: {int(y_va.sum())}")

    # --------------------------------------------------------------- eval model
    clf_eval = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf_eval.fit(X_tr, y_tr)
    y_pred = clf_eval.predict(X_va)

    print("\n=== Classification Report (stratified 25% val) ===")
    print(classification_report(y_va, y_pred, labels=[0, 1], target_names=["Normal", "Attack"]))
    cm = confusion_matrix(y_va, y_pred, labels=[0, 1])
    print("=== Confusion Matrix ===")
    print(f"  TN={cm[0,0]:4d}  FP={cm[0,1]:4d}")
    print(f"  FN={cm[1,0]:4d}  TP={cm[1,1]:4d}")

    importances = sorted(zip(ML_FEATURES, clf_eval.feature_importances_), key=lambda x: -x[1])
    print("\n=== Top 10 Feature Importances ===")
    for feat, imp in importances[:10]:
        print(f"  {feat:<8} {imp:.4f}")

    # ---------------------------------------------------------- final model (all data)
    clf_final = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    clf_final.fit(X, y)

    # ------------------------------------------------------------------ save
    model_path    = os.path.join(BASE_DIR, "anomaly_model.pkl")
    features_path = os.path.join(BASE_DIR, "feature_names.json")

    with open(model_path, "wb") as f:
        pickle.dump(clf_final, f)
    with open(features_path, "w") as f:
        json.dump(ML_FEATURES, f)

    print(f"\n[saved] model    → {model_path}")
    print(f"[saved] features → {features_path}")


if __name__ == "__main__":
    main()
