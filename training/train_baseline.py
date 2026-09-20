"""
Baseline Model Trainer for FraudGuard AI.

Architecture:
  - Feature Extractor: TF-IDF (Term Frequency-Inverse Document Frequency)
    capturing both word n-grams (1-2) and character n-grams (3-5).
  - Classifier: Multinomial Logistic Regression with balanced class weights.
  - Serialization: models/baseline_tfidf.joblib
  - Evaluation: Evaluated strictly on the held-out test set (data/splits/test.csv).
"""

import json
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "splits"
MODELS_DIR = BASE_DIR / "models"
EVAL_DIR = BASE_DIR / "evaluation"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)


def load_splits():
    """Load train, val, and test splits."""
    train_df = pd.read_csv(DATA_DIR / "train.csv")
    val_df = pd.read_csv(DATA_DIR / "val.csv")
    test_df = pd.read_csv(DATA_DIR / "test.csv")
    return train_df, val_df, test_df


def train_baseline_pipeline(train_df: pd.DataFrame) -> Pipeline:
    """
    Constructs and fits the baseline TF-IDF + Logistic Regression pipeline.
    Uses sublinear TF scaling and balanced class weighting.
    """
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=2,
                max_features=10000,
                strip_accents="unicode",
            ),
        ),
        (
            "clf",
            LogisticRegression(
                C=2.5,
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
                solver="lbfgs",
            ),
        ),
    ])

    print("Training Baseline Model (TF-IDF + Logistic Regression)...")
    pipeline.fit(train_df["text"], train_df["category"])
    return pipeline


def evaluate_pipeline(pipeline: Pipeline, test_df: pd.DataFrame):
    """
    Evaluates the model on the held-out test set and saves performance metrics.
    """
    y_true = test_df["category"]
    y_pred = pipeline.predict(test_df["text"])
    y_prob = pipeline.predict_proba(test_df["text"])

    labels = sorted(list(set(y_true)))

    acc = accuracy_score(y_true, y_pred)
    macro_p = precision_score(y_true, y_pred, average="macro", zero_division=0)
    macro_r = recall_score(y_true, y_pred, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    report_dict = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    report_text = classification_report(y_true, y_pred, zero_division=0)

    print("\n" + "=" * 65)
    print("Baseline Model (TF-IDF + Logistic Regression) Test Results")
    print("=" * 65)
    print(f"Overall Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"Macro Precision:   {macro_p:.4f}")
    print(f"Macro Recall:      {macro_r:.4f}")
    print(f"Macro F1-Score:    {macro_f1:.4f}")
    print(f"Weighted F1-Score: {weighted_f1:.4f}")
    print("=" * 65)
    print("\nDetailed Per-Category Classification Report:")
    print(report_text)

    # Save metrics JSON
    metrics_summary = {
        "model_name": "Baseline (TF-IDF + Logistic Regression)",
        "test_samples": len(test_df),
        "accuracy": round(acc, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": report_dict,
    }
    with open(EVAL_DIR / "baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Plot Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap="Blues", ax=ax, xticks_rotation=45)
    plt.title("Baseline Model: Confusion Matrix (Test Set)")
    plt.tight_layout()

    cm_path = MODELS_DIR / "baseline_confusion_matrix.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Saved Confusion Matrix visualization to: {cm_path}")


def main():
    train_df, val_df, test_df = load_splits()
    print(f"Loaded datasets: {len(train_df)} train, {len(val_df)} val, {len(test_df)} test.")

    pipeline = train_baseline_pipeline(train_df)

    # Save trained model artifact
    model_path = MODELS_DIR / "baseline_tfidf.joblib"
    joblib.dump(pipeline, model_path)
    print(f"Baseline model saved to: {model_path}")

    # Evaluate on test split
    evaluate_pipeline(pipeline, test_df)


if __name__ == "__main__":
    main()
