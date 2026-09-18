"""
Scam Classifier — two-tier approach:

Tier 1 (fast, no model needed):
  Rule-based keyword matcher using the scam taxonomy.
  Returns immediately if a category is matched with high confidence.

Tier 2 (higher accuracy, optional):
  Zero-shot classification via a HuggingFace NLI model.
  Falls back to rule-based result if the model isn't loaded.

The classifier is designed to be extended with a fine-tuned model
(trained on the Kaggle SMS-Spam Collection + labelled Indian scam SMS data).
"""
import re
from functools import lru_cache
from typing import Optional

from core.logging import logger
from core.models import ScamClassification, ScamCategory, RiskLevel
from classification.taxonomy import SCAM_TAXONOMY, CATEGORY_TO_DEF, ScamDefinition

# ─── Risk level → RiskLevel enum ─────────────────────────────────────────────

_RISK_MAP = {
    "high": RiskLevel.HIGH,
    "medium": RiskLevel.MEDIUM,
    "low": RiskLevel.LOW,
    "safe": RiskLevel.SAFE,
}


def _build_result(defn: ScamDefinition, confidence: float, indicators: list[str]) -> ScamClassification:
    return ScamClassification(
        category=ScamCategory(defn.category),
        confidence=round(confidence, 3),
        risk_level=_RISK_MAP.get(defn.risk_level, RiskLevel.MEDIUM),
        label_display=defn.label,
        indicators=indicators,
    )


# ─── Tier 1: Rule-Based ───────────────────────────────────────────────────────

def _keyword_score(text: str, defn: ScamDefinition) -> tuple[float, list[str]]:
    """
    Returns (normalised_score, matched_keywords).
    Score = matched / total_keywords, capped between 0 and 1.
    """
    text_lower = text.lower()
    matched = [kw for kw in defn.keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    if not matched:
        return 0.0, []
    score = min(1.0, 0.4 + (len(matched) / max(len(defn.keywords), 1)) * 0.6)
    return score, matched


def rule_based_classify(text: str) -> ScamClassification:
    """Fast keyword-based classification."""
    best_score = 0.0
    best_defn: Optional[ScamDefinition] = None
    best_indicators: list[str] = []

    for defn in SCAM_TAXONOMY:
        score, indicators = _keyword_score(text, defn)
        if score > best_score:
            best_score = score
            best_defn = defn
            best_indicators = indicators

    if best_defn is None or best_score < 0.2:
        return ScamClassification(
            category=ScamCategory.UNKNOWN,
            confidence=0.0,
            risk_level=RiskLevel.LOW,
            label_display="Unknown / Review Needed",
            indicators=[],
        )

    return _build_result(best_defn, best_score, best_indicators)


# ─── Tier 2: Zero-Shot NLI Classifier ────────────────────────────────────────

class ZeroShotScamClassifier:
    """
    Uses a HuggingFace NLI model for zero-shot text classification.
    Loaded lazily — if torch or transformers are not installed the classifier
    silently falls back to rule-based results without crashing.
    """

    _pipeline = None
    _CANDIDATE_LABELS = [d.label for d in SCAM_TAXONOMY]

    @classmethod
    def _get_pipeline(cls):
        if cls._pipeline is None:
            try:
                import torch  # noqa: F401  — check availability first
                from transformers import pipeline as hf_pipeline
                cls._pipeline = hf_pipeline(
                    "zero-shot-classification",
                    model="cross-encoder/nli-MiniLM2-L6-H768",
                    device=-1,  # CPU
                )
                logger.info("classifier.zeroshot_loaded")
            except ImportError:
                logger.warning("classifier.zeroshot_unavailable", reason="torch/transformers not installed — using rule-based only")
                cls._pipeline = False  # Mark as permanently unavailable
            except Exception as exc:  # noqa: BLE001
                logger.warning("classifier.zeroshot_failed", error=str(exc))
                cls._pipeline = False
        return cls._pipeline

    @classmethod
    def classify(cls, text: str) -> Optional[ScamClassification]:
        pipe = cls._get_pipeline()
        if not pipe:
            return None

        try:
            result = pipe(
                text[:512],
                candidate_labels=cls._CANDIDATE_LABELS,
                multi_label=False,
            )
            top_label: str = result["labels"][0]
            top_score: float = result["scores"][0]

            # Map label back to category definition
            defn = next(
                (d for d in SCAM_TAXONOMY if d.label == top_label), None
            )
            if defn is None or top_score < 0.3:
                return None

            return _build_result(defn, top_score, [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("classifier.zeroshot_error", error=str(exc))
            return None


# ─── Public Interface ─────────────────────────────────────────────────────────

def classify_text(text: str, use_ml: bool = True) -> ScamClassification:
    """
    Classify `text` into a scam category.

    Strategy:
    1. Run rule-based classifier.
    2. If ML is enabled AND rule-based confidence is low (<0.55), try zero-shot.
    3. Return whichever has higher confidence.
    """
    rule_result = rule_based_classify(text)

    if use_ml and rule_result.confidence < 0.55:
        ml_result = ZeroShotScamClassifier.classify(text)
        if ml_result and ml_result.confidence > rule_result.confidence:
            # Merge indicators from rule-based into ML result
            ml_result.indicators = rule_result.indicators
            return ml_result

    return rule_result
