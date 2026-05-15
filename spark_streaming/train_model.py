"""
Phase 3.5 — ML Early Warning: Random Forest Anomaly Detector
Train on BATADAL_dataset03 (+synthetic if present), evaluate on dataset04.
Saves anomaly_model.pkl + feature_names.json to spark_streaming/ directory.

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
    return df


def main():
    # ------------------------------------------------------------------ data
    train_paths = [os.path.join(DATASET_DIR, "BATADAL_dataset03.csv")]
    synthetic   = os.path.join(DATASET_DIR, "BATADAL_synthetic.csv")
    if os.path.exists(synthetic):
        train_paths.append(synthetic)
        print(f"[info] Including synthetic dataset: {synthetic}")

    df_train = pd.concat([load_csv(p) for p in train_paths], ignore_index=True)
    df_test  = load_csv(os.path.join(DATASET_DIR, "BATADAL_dataset04.csv"))

    X_train = df_train[ML_FEATURES].fillna(0.0)
    y_train = df_train["ATT_FLAG"]
    X_test  = df_test[ML_FEATURES].fillna(0.0)
    y_test  = df_test["ATT_FLAG"]

    n_att_tr = int(y_train.sum())
    n_att_te = int(y_test.sum())
    print(f"Train : {len(df_train):>6} rows | attacks {n_att_tr} ({100*y_train.mean():.1f}%)")
    print(f"Test  : {len(df_test):>6} rows | attacks {n_att_te} ({100*y_test.mean():.1f}%)")

    # ----------------------------------------------------------------- train
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        class_weight="balanced",   # handles class imbalance (attacks are minority)
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    # --------------------------------------------------------------- evaluate
    y_pred = clf.predict(X_test)
    print("\n=== Classification Report (dataset04) ===")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Attack"]))
    print("=== Confusion Matrix ===")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}  TP={cm[1,1]}")

    importances = sorted(zip(ML_FEATURES, clf.feature_importances_), key=lambda x: -x[1])
    print("\n=== Top 10 Feature Importances ===")
    for feat, imp in importances[:10]:
        print(f"  {feat:<8} {imp:.4f}")

    # ------------------------------------------------------------------ save
    model_path    = os.path.join(BASE_DIR, "anomaly_model.pkl")
    features_path = os.path.join(BASE_DIR, "feature_names.json")

    with open(model_path, "wb") as f:
        pickle.dump(clf, f)
    with open(features_path, "w") as f:
        json.dump(ML_FEATURES, f)

    print(f"\n[saved] model    → {model_path}")
    print(f"[saved] features → {features_path}")


if __name__ == "__main__":
    main()
