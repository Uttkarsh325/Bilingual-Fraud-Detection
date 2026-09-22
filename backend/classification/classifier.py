"""
Scam Classifier for FraudGuard AI.

Tiered Classification Architecture:
  Tier 1 (Fine-tuned Transformer - Production):
    DistilBERT sequence classifier fine-tuned on the Indian financial fraud taxonomy
    dataset (models/advanced_classifier). Returns predicted category, probability
    confidence, and detected trigger indicators.

  Tier 2 (Trained ML Model - Fallback):
    Loads serialized ML models (TF-IDF + Logistic Regression or XGBoost) trained on
    the same dataset when the transformer is unavailable.

  Tier 3 (Zero-shot NLI Model - Optional Fallback):
    HuggingFace zero-shot NLI pipeline when torch/transformers are loaded.

  Tier 4 (Rule-Based Matcher - Resilient Fallback):
    Fast regex and keyword matcher ensuring the service never fails even in zero-dependency environments.
"""

from pathlib import Path
import re
from typing import Optional
import joblib
import numpy as np

from classification.taxonomy import CATEGORY_TO_DEF, SCAM_TAXONOMY, ScamDefinition, _combined_keywords
from core.logging import logger
from core.models import RiskLevel, ScamCategory, ScamClassification

# ─── Risk level mapping ───────────────────────────────────────────────────────

_RISK_MAP = {
    "high": RiskLevel.HIGH,
    "medium": RiskLevel.MEDIUM,
    "low": RiskLevel.LOW,
    "safe": RiskLevel.SAFE,
}

# Minimum confidence an ML verdict must hit before we surface a scam call that
# carries no matched indicators. Models are sometimes confidently wrong on
# out-of-distribution input; a scam verdict should be backed by evidence.
_MIN_CONFIDENCE_NO_INDICATORS = 0.7

# Script ranges the fine-tuned models were never trained on. When a message is
# written in one of these (e.g. Devanagari), the English-trained DistilBERT /
# TF-IDF output is out-of-distribution noise, so a scam verdict is only trusted
# when it is corroborated by matched taxonomy indicators.
_NON_LATIN_SCRIPT_RANGES = [
    (r"[\u0900-\u097F]", "Devanagari"),  # Hindi, Marathi, Nepali, Sanskrit
    (r"[\u0980-\u09FF]", "Bengali"),
    (r"[\u0A00-\u0A7F]", "Gurmukhi"),
    (r"[\u0A80-\u0AFF]", "Gujarati"),
    (r"[\u0B00-\u0B7F]", "Oriya"),
    (r"[\u0B80-\u0BFF]", "Tamil"),
    (r"[\u0C00-\u0C7F]", "Telugu"),
    (r"[\u0C80-\u0CFF]", "Kannada"),
    (r"[\u0D00-\u0D7F]", "Malayalam"),
    (r"[\u0600-\u06FF]", "Arabic"),
    (r"[\u0E00-\u0E7F]", "Thai"),
    (r"[\u0F00-\u0FFF]", "Tibetan"),
    (r"[\u2000-\u206F]", "Arabic_Presentation"),
]

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


def _is_non_latin_script(text: str) -> bool:
    """True if the message is written (at least partly) in a non-Latin script."""
    for pattern, _name in _NON_LATIN_SCRIPT_RANGES:
        if re.search(pattern, text):
            return True
    return False


def _gate_ml_verdict(
    result: Optional[ScamClassification], text: str
) -> Optional[ScamClassification]:
    """Reject unreliably-sourced ML verdicts (guard against OOD model noise).

    Safe/unknown/benign outcomes always pass on in-distribution (Latin-script)
    input. On out-of-distribution (non-Latin) input the model output is noise,
    so a verdict is only trusted when it is corroborated by matched indicators
    or carries high confidence. Unsure low-confidence \"benign\" guesses on
    Hindi messages are dropped so the tier ladder can fall through to the
    rule-based matcher (which now understands Devanagari keywords).
    """
    if result is None:
        return None

    is_safe = (
        result.risk_level == RiskLevel.SAFE
        or result.category in (ScamCategory.BENIGN, ScamCategory.UNKNOWN)
    )
    if result.indicators:
        return result

    if not _is_non_latin_script(text):
        # In-distribution: trust the model (safe verdicts included).
        return result

    # Out-of-distribution (e.g. Devanagari) — require corroboration or
    # high confidence, even for a "benign" verdict.
    if is_safe and result.confidence >= _MIN_CONFIDENCE_NO_INDICATORS:
        return result

    logger.debug("classifier.gated_ood_verdict", category=result.category.value)
    return None


def _extract_indicators(text: str, category: Optional[str] = None) -> list[str]:
    """Extract matched trigger keywords and risk indicators from text."""
    text_lower = text.lower()
    matched = []

    # Check category specific keywords first
    if category and category in CATEGORY_TO_DEF:
        defn = CATEGORY_TO_DEF[category]
        for kw in _combined_keywords(defn):
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                matched.append(kw)

    # General financial urgency indicators
    urgency_patterns = [
        ("urgent", r"\b(urgent|immediately|immediately|expire|blocked|suspend|today|24 hours)\b"),
        ("credential_demand", r"\b(otp|pin|password|cvv|aadhaar|pan)\b"),
        ("external_link", r"(https?://\S+|bit\.ly/\S+|tinyurl\.com/\S+)"),
        ("unrealistic_money", r"\b(lottery|winner|jackpot|guaranteed return|double money)\b"),
        ("authority_impersonation", r"\b(police|cbi|rbi|trai|customs|inspector)\b"),
    ]

    for label, pat in urgency_patterns:
        if re.search(pat, text_lower) and label not in matched:
            matched.append(label)

    return list(dict.fromkeys(matched))  # Deduplicate preserving order


def _build_result(defn: ScamDefinition, confidence: float, indicators: list[str]) -> ScamClassification:
    return ScamClassification(
        category=ScamCategory(defn.category),
        confidence=round(confidence, 3),
        risk_level=_RISK_MAP.get(defn.risk_level, RiskLevel.MEDIUM),
        label_display=defn.label,
        indicators=indicators,
    )


# ─── Tier 1: Fine-Tuned Transformer Classifier (Primary) ──────────────────────

class TransformerScamClassifier:
    """Loads and serves inference from the fine-tuned DistilBERT model in models/advanced_classifier/."""

    MODEL_PATH = MODELS_DIR / "advanced_classifier"
    _model = None
    _tokenizer = None

    @classmethod
    def _ensure_loaded(cls):
        if cls._model is None and cls.MODEL_PATH.exists() and (cls.MODEL_PATH / "model.safetensors").exists():
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                cls._tokenizer = AutoTokenizer.from_pretrained(str(cls.MODEL_PATH))
                cls._model = AutoModelForSequenceClassification.from_pretrained(str(cls.MODEL_PATH))
                logger.info("classifier.transformer_loaded", path=str(cls.MODEL_PATH))
            except Exception as exc:
                logger.warning("classifier.transformer_load_failed", error=str(exc))
                cls._model = False
        return cls._model

    @classmethod
    def classify(cls, text: str) -> Optional[ScamClassification]:
        model = cls._ensure_loaded()
        if model is None or model is False:
            return None

        try:
            import torch

            inputs = cls._tokenizer(
                text[:512],
                truncation=True,
                padding=True,
                max_length=128,
                return_tensors="pt",
            )
            with torch.inference_mode():
                logits = model(**inputs).logits

            probs = torch.softmax(logits[0], dim=-1)
            pred_idx = int(torch.argmax(probs))
            confidence = float(probs[pred_idx])

            id2label = model.config.id2label
            pred_category = id2label.get(pred_idx) or id2label.get(str(pred_idx))

            defn = CATEGORY_TO_DEF.get(pred_category)
            if defn is None:
                return None

            indicators = _extract_indicators(text, pred_category)
            return _build_result(defn, confidence, indicators)

        except Exception as exc:
            logger.warning("classifier.transformer_inference_error", error=str(exc))
            return None


# ─── Tier 2: Trained ML Classifier (Fallback) ─────────────────────────────────

class TrainedScamClassifier:
    """Loads and serves inference from the trained model artifacts in models/."""

    _model = None
    _model_type = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # 1. Try Baseline TF-IDF (Fastest, ~99% accuracy on benchmark)
            baseline_path = MODELS_DIR / "baseline_tfidf.joblib"
            if baseline_path.exists():
                try:
                    cls._model = joblib.load(baseline_path)
                    cls._model_type = "baseline_tfidf"
                    logger.info("classifier.loaded_trained_baseline", path=str(baseline_path))
                    return cls._model
                except Exception as exc:
                    logger.warning("classifier.load_baseline_failed", error=str(exc))

            # 2. Try Advanced XGBoost
            advanced_path = MODELS_DIR / "advanced_xgboost.joblib"
            if advanced_path.exists():
                try:
                    cls._model = joblib.load(advanced_path)
                    cls._model_type = "advanced_xgboost"
                    logger.info("classifier.loaded_trained_advanced", path=str(advanced_path))
                    return cls._model
                except Exception as exc:
                    logger.warning("classifier.load_advanced_failed", error=str(exc))

        return cls._model

    @classmethod
    def classify(cls, text: str) -> Optional[ScamClassification]:
        model = cls.get_model()
        if model is None:
            return None

        try:
            if cls._model_type == "baseline_tfidf":
                # Scikit-learn Pipeline
                pred_category = model.predict([text])[0]
                proba = model.predict_proba([text])[0]
                confidence = float(np.max(proba))

            elif cls._model_type == "advanced_xgboost":
                # XGBoost Pipeline with mapping
                pipeline = model["pipeline"]
                idx_to_label = model["idx_to_label"]
                pred_idx = pipeline.predict([text])[0]
                pred_category = idx_to_label[pred_idx]
                proba = pipeline.predict_proba([text])[0]
                confidence = float(np.max(proba))
            else:
                return None

            defn = CATEGORY_TO_DEF.get(pred_category)
            if defn is None:
                return None

            indicators = _extract_indicators(text, pred_category)

            # Calibrate confidence: if key domain indicators are present, fuse ML probability with indicator strength
            if indicators and defn.category != "benign":
                indicator_weight = min(0.95, 0.45 + (len(indicators) / max(len(defn.keywords), 1)) * 0.55)
                confidence = max(confidence, indicator_weight)

            return _build_result(defn, confidence, indicators)

        except Exception as exc:
            logger.warning("classifier.trained_inference_error", error=str(exc))
            return None


# ─── Tier 3: Zero-Shot NLI Classifier (Optional) ──────────────────────────────

class ZeroShotScamClassifier:
    """Uses HuggingFace NLI model for zero-shot text classification if available."""

    _pipeline = None
    _CANDIDATE_LABELS = [d.label for d in SCAM_TAXONOMY if d.category != "benign"]

    @classmethod
    def _get_pipeline(cls):
        if cls._pipeline is None:
            try:
                from transformers import pipeline as hf_pipeline
                cls._pipeline = hf_pipeline(
                    "zero-shot-classification",
                    model="cross-encoder/nli-MiniLM2-L6-H768",
                    device=-1,
                )
                logger.info("classifier.zeroshot_loaded")
            except Exception as exc:
                logger.warning("classifier.zeroshot_unavailable", reason=str(exc))
                cls._pipeline = False
        return cls._pipeline

    @classmethod
    def classify(cls, text: str) -> Optional[ScamClassification]:
        pipe = cls._get_pipeline()
        if not pipe:
            return None

        try:
            result = pipe(text[:512], candidate_labels=cls._CANDIDATE_LABELS, multi_label=False)
            top_label: str = result["labels"][0]
            top_score: float = result["scores"][0]

            defn = next((d for d in SCAM_TAXONOMY if d.label == top_label), None)
            if defn is None or top_score < 0.3:
                return None

            indicators = _extract_indicators(text, defn.category)
            return _build_result(defn, top_score, indicators)
        except Exception as exc:
            logger.warning("classifier.zeroshot_error", error=str(exc))
            return None


# ─── Tier 4: Rule-Based Fallback ──────────────────────────────────────────────

def rule_based_classify(text: str) -> ScamClassification:
    """Keyword-based classification fallback (English + Devanagari Hindi)."""
    text_lower = text.lower()
    best_score = 0.0
    best_defn: Optional[ScamDefinition] = None
    best_indicators: list[str] = []

    for defn in SCAM_TAXONOMY:
        all_kw = _combined_keywords(defn)
        matched = [kw for kw in all_kw if re.search(r"\b" + re.escape(kw) + r"\b", text_lower)]
        if matched:
            score = min(1.0, 0.4 + (len(matched) / max(len(all_kw), 1)) * 0.6)
            if score > best_score:
                best_score = score
                best_defn = defn
                best_indicators = matched

    if best_defn is None or best_score < 0.2:
        return ScamClassification(
            category=ScamCategory.UNKNOWN,
            confidence=0.0,
            risk_level=RiskLevel.LOW,
            label_display="Unknown / Needs Review",
            indicators=_extract_indicators(text),
        )

    all_indicators = _extract_indicators(text, best_defn.category)
    return _build_result(best_defn, best_score, all_indicators)


# ─── Public Interface ─────────────────────────────────────────────────────────

def _rule_based_evidence(text: str) -> Optional[ScamClassification]:
    """Run the keyword matcher as an evidence scan (script-agnostic)."""
    res = rule_based_classify(text)
    if res.category in (ScamCategory.BENIGN, ScamCategory.UNKNOWN):
        return None
    return res


def _resolve_rule_override(
    ml: ScamClassification | None,
    rule: ScamClassification | None,
    text: str,
) -> ScamClassification | None:
    """Prefer concrete rule-based evidence over weak/uncertain ML verdicts.

    - A confident, evidence-backed ML call always wins.
    - On in-distribution (Latin-script) input, a high-confidence ML verdict is
      trusted even without matched indicators (e.g. a confident ``sim_swap``
      call the keyword matcher can't corroborate).
    - On out-of-distribution (non-Latin) input the ML categories are model
      guesswork, so concrete matched indicators (e.g. ``cashback``/
      ``लिंक``) win over an unevidenced ML guess.

    A confident ML ``benign`` verdict is respected: legit messages that merely
    contain a loose keyword (e.g. a genuine OTP login SMS) must not be
    re-flagged as scams.
    """
    if ml is None:
        return rule
    if rule is None:
        return ml

    ml_is_benign = ml.category in (ScamCategory.BENIGN, ScamCategory.UNKNOWN)
    ml_is_confident = ml.confidence >= _MIN_CONFIDENCE_NO_INDICATORS
    ml_is_confident_scam = (
        not ml_is_benign and ml.indicators and ml_is_confident
    )
    if ml_is_confident_scam:
        return ml

    # In-distribution high-confidence ML verdict — trust it over loose keywords.
    if ml_is_confident and not _is_non_latin_script(text):
        return ml

    if ml_is_benign:
        return rule

    if not ml.indicators or ml.confidence < 0.5:
        return rule

    return ml


def classify_text(text: str, use_ml: bool = True) -> ScamClassification:
    """
    Main classification function called by API and LangGraph pipeline.

    Execution Strategy:
      1. Try the fine-tuned transformer model (DistilBERT, models/advanced_classifier).
      2. Try the trained production ML models (TF-IDF / XGBoost).
      3. Try Zero-Shot NLI.
      4. If ML fails or is disabled, fall back to rule-based classification.

    Every ML verdict is evidence-gated (see _gate_ml_verdict), and concrete
    rule-based keyword hits override weak/uncertain ML outcomes (see
    _resolve_rule_override).
    """
    if use_ml:
        # 1. Fine-tuned transformer (primary)
        tf_result = _gate_ml_verdict(_resolve_rule_override(
            TransformerScamClassifier.classify(text), _rule_based_evidence(text), text
        ), text)
        if tf_result is not None:
            return tf_result

        # 2. Trained TF-IDF / XGBoost fallback
        ml_result = _gate_ml_verdict(_resolve_rule_override(
            TrainedScamClassifier.classify(text), _rule_based_evidence(text), text
        ), text)
        if ml_result is not None:
            return ml_result

        # 3. Zero-shot if trained models missing
        zs_result = _gate_ml_verdict(_resolve_rule_override(
            ZeroShotScamClassifier.classify(text), _rule_based_evidence(text), text
        ), text)
        if zs_result is not None:
            return zs_result

    # Final fallback
    return rule_based_classify(text)
