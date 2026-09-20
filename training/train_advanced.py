"""
Advanced Model Trainer for FraudGuard AI — Gradient Boosted Decision Forest (XGBoost).

Architecture:
  - Feature Engineering: Combined Word (1-3 n-grams) and Sub-word Character (3-5 n-grams)
    TF-IDF with sublinear scaling and L2 normalization.
  - Classifier: Multi-class XGBoost with log-loss objective and multi-tree ensemble.
  - Evaluation: Evaluated on the exact same held-out test set (data/splits/test.csv).
  - Artifacts: models/advanced_xgboost.joblib, models/advanced_confusion_matrix.png
"""

import json
from pathlib import Path
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import FeatureUnion, Pipeline
from xgboost import XGBClassifier

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


def build_advanced_pipeline(labels: list[str]) -> tuple[Pipeline, dict[str, int]]:
    """
    Builds an advanced feature extraction union (Word + Char n-grams)
    and couples it with a multi-class XGBoost classifier.
    """
    label_to_idx = {lbl: i for i, lbl in enumerate(labels)}
    idx_to_label = {i: lbl for i, lbl in enumerate(labels)}

    # Feature union combines word-level semantics with sub-word character patterns
    # Sub-word char n-grams excel at capturing obfuscated URLs, typo spam, and Indian phone patterns
    features = FeatureUnion([
        (
            "word_tfidf",
            TfidfVectorizer(
                ngram_range=(1, 3),
                analyzer="word",
                sublinear_tf=True,
                max_features=8000,
                strip_accents="unicode",
            ),
        ),
        (
            "char_tfidf",
            TfidfVectorizer(
                ngram_range=(3, 5),
                analyzer="char_wb",
                sublinear_tf=True,
                max_features=12000,
            ),
        ),
    ])

    xgb = XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=len(labels),
        random_state=42,
        tree_method="hist",
        n_jobs=-1,
    )

    pipeline = Pipeline([
        ("features", features),
        ("xgb", xgb),
    ])

    return pipeline, label_to_idx


def evaluate_advanced_model(pipeline: Pipeline, test_df: pd.DataFrame, label_to_idx: dict[str, int]):
    """Evaluate on the held-out test split."""
    idx_to_label = {v: k for k, v in label_to_idx.items()}
    labels = [idx_to_label[i] for i in range(len(label_to_idx))]

    y_true_str = test_df["category"].tolist()
    y_true_idx = [label_to_idx[cat] for cat in y_true_str]

    y_pred_idx = pipeline.predict(test_df["text"])
    y_pred_str = [idx_to_label[idx] for idx in y_pred_idx]

    acc = accuracy_score(y_true_str, y_pred_str)
    macro_p = precision_score(y_true_str, y_pred_str, average="macro", zero_division=0)
    macro_r = recall_score(y_true_str, y_pred_str, average="macro", zero_division=0)
    macro_f1 = f1_score(y_true_str, y_pred_str, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true_str, y_pred_str, average="weighted", zero_division=0)

    report_dict = classification_report(y_true_str, y_pred_str, output_dict=True, zero_division=0)
    report_text = classification_report(y_true_str, y_pred_str, zero_division=0)

    print("\n" + "=" * 65)
    print("Advanced Model (FeatureUnion + XGBoost) Test Results")
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
        "model_name": "Advanced (FeatureUnion + XGBoost)",
        "test_samples": len(test_df),
        "accuracy": round(acc, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": report_dict,
    }
    with open(EVAL_DIR / "advanced_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Plot Confusion Matrix
    cm = confusion_matrix(y_true_str, y_pred_str, labels=labels)
    fig, ax = plt.subplots(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(cmap="Greens", ax=ax, xticks_rotation=45)
    plt.title("Advanced Model: Confusion Matrix (Test Set)")
    plt.tight_layout()

    cm_path = MODELS_DIR / "advanced_confusion_matrix.png"
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Saved Confusion Matrix visualization to: {cm_path}")


def main():
    train_df, val_df, test_df = load_splits()
    labels = sorted(list(set(train_df["category"])))

    pipeline, label_to_idx = build_advanced_pipeline(labels)

    y_train_idx = [label_to_idx[cat] for cat in train_df["category"]]

    print("Training Advanced Model (Multi-feature Union + XGBoost)...")
    pipeline.fit(train_df["text"], y_train_idx)

    # Save model artifact and label mapping
    model_artifact = {
        "pipeline": pipeline,
        "label_to_idx": label_to_idx,
        "idx_to_label": {v: k for k, v in label_to_idx.items()},
    }
    model_path = MODELS_DIR / "advanced_xgboost.joblib"
    joblib.dump(model_artifact, model_path)
    print(f"Advanced model saved to: {model_path}")

    # Evaluate on held-out test split
    evaluate_advanced_model(pipeline, test_df, label_to_idx)


if __name__ == "__main__":
    main()
