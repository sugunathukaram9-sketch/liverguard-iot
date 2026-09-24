"""
Liver Risk Prediction - Model Training Pipeline
================================================
Dataset : Indian Liver Patient Records (ILPD) - Kaggle: uciml/indian-liver-patient-records
          (UCI ML Repository #225, 583 records, donated by B. Ramana & N. Venkateswarlu)

Every feature below is a biochemical / physiological parameter that can be
acquired with IoT-compatible biosensor modules, which is why this dataset is
ideal for an IoT-integrated final review:

    Age, Gender          -> patient profile (stored on device)
    Total Bilirubin      -> optical / colorimetric bilirubin sensor (like a
    Direct Bilirubin        transcutaneous bilirubinometer - non-invasive light sensor)
    Alkaline Phosphotase -> electrochemical enzyme biosensor
    ALT (SGPT)           -> electrochemical enzyme biosensor
    AST (SGOT)           -> electrochemical enzyme biosensor
    Total Proteins       -> bio-impedance / potentiometric protein sensor
    Albumin              -> albumin biosensor (immuno / electrochemical)
    A/G Ratio            -> computed on the MCU from Albumin & Globulin readings
"""

import json
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (GradientBoostingClassifier,
                              RandomForestClassifier, VotingClassifier)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

RANDOM_STATE = 42
DATA_PATH = "data/ilpd.csv"
MODEL_PATH = "model/liver_model.pkl"
REPORT_PATH = "model/training_report.json"

COLUMN_NAMES = [
    "Age", "Gender", "Total_Bilirubin", "Direct_Bilirubin",
    "Alkaline_Phosphotase", "Alamine_Aminotransferase",
    "Aspartate_Aminotransferase", "Total_Protiens", "Albumin",
    "Albumin_and_Globulin_Ratio", "Dataset",
]

FEATURE_COLUMNS = COLUMN_NAMES[:-1]


def load_and_clean():
    df = pd.read_csv(DATA_PATH, names=COLUMN_NAMES)

    # --- basic cleaning -------------------------------------------------
    df = df.dropna(subset=["Albumin"])            # a handful of rows miss albumin+ratio
    df["Albumin_and_Globulin_Ratio"] = df["Albumin_and_Globulin_Ratio"].fillna(
        df["Albumin"] / (df["Total_Protiens"] - df["Albumin"]).replace(0, np.nan)
    )
    df["Albumin_and_Globulin_Ratio"] = df["Albumin_and_Globulin_Ratio"].fillna(
        df["Albumin_and_Globulin_Ratio"].median()
    )

    # derived ratio sanity guard
    df["Albumin_and_Globulin_Ratio"] = df["Albumin_and_Globulin_Ratio"].clip(lower=0)

    # --- encoding -------------------------------------------------------
    df["Gender_Male"] = (df["Gender"].str.strip().str.lower() == "male").astype(int)
    # label: 1 = liver patient, 2 = healthy  ->  1 = risk, 0 = healthy
    df["Risk"] = (df["Dataset"] == 1).astype(int)

    # extra informative features an MCU could compute on the fly
    df["Bilirubin_Ratio"] = df["Direct_Bilirubin"] / df["Total_Bilirubin"].replace(0, np.nan)
    df["Bilirubin_Ratio"] = df["Bilirubin_Ratio"].fillna(0)
    df["AST_ALT_Ratio"] = df["Aspartate_Aminotransferase"] / df["Alamine_Aminotransferase"].replace(0, np.nan)
    df["AST_ALT_Ratio"] = df["AST_ALT_Ratio"].replace([np.inf, -np.inf], 0).fillna(1)
    df["Protein_Albumin_Diff"] = df["Total_Protiens"] - df["Albumin"]

    return df


def main():
    df = load_and_clean()
    print(f"Dataset loaded: {df.shape[0]} records, class balance -> "
          f"{int(df['Risk'].sum())} patients / {int((df['Risk'] == 0).sum())} healthy\n")

    feature_cols = [
        "Age", "Gender_Male", "Total_Bilirubin", "Direct_Bilirubin",
        "Alkaline_Phosphotase", "Alamine_Aminotransferase",
        "Aspartate_Aminotransferase", "Total_Protiens", "Albumin",
        "Albumin_and_Globulin_Ratio", "Bilirubin_Ratio", "AST_ALT_Ratio",
        "Protein_Albumin_Diff",
    ]

    X = df[feature_cols].values
    y = df["Risk"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
    )

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    candidates = {
        "Logistic Regression": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=2000)),
        ]),
        "Random Forest": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(n_estimators=400, class_weight="balanced_subsample",
                                           random_state=RANDOM_STATE)),
        ]),
        "Gradient Boosting": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", GradientBoostingClassifier(random_state=RANDOM_STATE)),
        ]),
        "XGBoost": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.05,
                                  subsample=0.9, colsample_bytree=0.9,
                                  reg_lambda=1.5, eval_metric="logloss",
                                  random_state=RANDOM_STATE)),
        ]),
        "SVM (RBF)": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", SVC(kernel="rbf", class_weight="balanced", probability=True,
                        random_state=RANDOM_STATE)),
        ]),
        "KNN": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("sc", StandardScaler()),
            ("clf", KNeighborsClassifier(n_neighbors=11)),
        ]),
    }

    print(f"{'Model':<24}{'CV Accuracy':>12}{'CV AUC':>10}")
    print("-" * 46)
    results = {}
    for name, pipe in candidates.items():
        from sklearn.model_selection import cross_val_score
        acc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="accuracy")
        auc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc")
        results[name] = {"cv_acc": float(acc.mean()), "cv_auc": float(auc.mean()), "pipe": pipe}
        print(f"{name:<24}{acc.mean():>12.4f}{auc.mean():>10.4f}")

    best_name = max(results, key=lambda k: (results[k]["cv_auc"], results[k]["cv_acc"]))
    print(f"\nBest single model by CV AUC: {best_name}")

    # --- fine-tune the winner ------------------------------------------------
    if best_name == "XGBoost":
        grid = GridSearchCV(
            results[best_name]["pipe"],
            {"clf__max_depth": [3, 4, 5], "clf__learning_rate": [0.03, 0.05, 0.08],
             "clf__min_child_weight": [1, 3], "clf__n_estimators": [300, 500]},
            cv=cv, scoring="roc_auc", n_jobs=-1,
        ).fit(X_train, y_train)
        best_pipe = grid.best_estimator_
        print("Tuned XGBoost params:", grid.best_params_)
    else:
        best_pipe = results[best_name]["pipe"].fit(X_train, y_train)

    # --- ensemble of top models (soft voting) --------------------------------
    ensemble = VotingClassifier(
        estimators=[
            ("xgb", results["XGBoost"]["pipe"]),
            ("gb", results["Gradient Boosting"]["pipe"]),
            ("rf", results["Random Forest"]["pipe"]),
            ("svm", results["SVM (RBF)"]["pipe"]),
        ],
        voting="soft", weights=[2, 1, 1, 1],
    ).fit(X_train, y_train)

    # --- final comparison on held-out test set -------------------------------
    final_candidates = {"Best single (tuned)": best_pipe, "Ensemble": ensemble}
    print(f"\n{'Final model':<22}{'Acc':>8}{'Prec':>8}{'Recall':>8}{'F1':>8}{'AUC':>8}")
    print("-" * 62)
    best_final, best_final_auc, best_final_name = None, -1, ""
    report_rows = []
    for name, model in final_candidates.items():
        pred = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        m = {
            "model": name,
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision": float(precision_score(y_test, pred)),
            "recall": float(recall_score(y_test, pred)),
            "f1": float(f1_score(y_test, pred)),
            "auc": float(roc_auc_score(y_test, proba)),
            "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        }
        report_rows.append(m)
        print(f"{name:<22}{m['accuracy']:>8.4f}{m['precision']:>8.4f}"
              f"{m['recall']:>8.4f}{m['f1']:>8.4f}{m['auc']:>8.4f}")
        if m["auc"] > best_final_auc:
            best_final, best_final_auc, best_final_name = model, m["auc"], name

    print(f"\n>>> DEPLOYED MODEL: {best_final_name}")
    print(classification_report(y_test, best_final.predict(X_test),
                                target_names=["Healthy (0)", "Liver Patient (1)"]))

    joblib.dump({"model": best_final, "feature_columns": feature_cols}, MODEL_PATH)
    print(f"Model saved -> {MODEL_PATH}")

    with open(REPORT_PATH, "w") as f:
        json.dump({
            "dataset": "Indian Liver Patient Records (ILPD) - Kaggle uciml/indian-liver-patient-records",
            "n_records": int(df.shape[0]),
            "n_features": len(feature_cols),
            "feature_columns": feature_cols,
            "cv_results": {k: {"cv_accuracy": v["cv_acc"], "cv_auc": v["cv_auc"]}
                           for k, v in results.items()},
            "final_results": report_rows,
            "deployed_model": best_final_name,
        }, f, indent=2)
    print(f"Training report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
