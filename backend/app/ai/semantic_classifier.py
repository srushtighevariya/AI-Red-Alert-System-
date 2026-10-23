"""AI model that reads the meaning of the text, not just keywords.

Uses a multilingual zero-shot NLI model (default: mDeBERTa-v3 trained on
multilingual NLI). Each chunk of the document is compared against short
descriptions ("a scam that tricks someone into paying money", ...) plus one
for ordinary content; the labels compete (softmax), and a risky label only
counts when the model is very sure (SEMANTIC_THRESHOLD). It understands
paraphrases the keyword lists miss ("keep this payment out of the books") and
reads Gujarati as well as English.

Measured on hand-written test sentences: at 0.75 no safe text was flagged and
5 of 9 paraphrased risks were caught. It is a high-confidence extra signal on
top of the rules, not a replacement for them.

Optional: if torch/transformers are not installed, or the model cannot be
loaded, classify() returns status "unavailable" and the app keeps working with
the rule-based detectors only.
"""

import logging
import threading

from app.ai.sentences import sentence_spans
from app.core.config import settings

logger = logging.getLogger(__name__)

HYPOTHESIS_TEMPLATE = "This text is about {}."

# Competes with the risky labels so ordinary text has somewhere to go.
NEUTRAL_HYPOTHESIS = "ordinary business, legal, news or personal information"

# key -> what the model is asked, and how the signal is shown to users.
# Wordings were chosen by testing several phrasings against safe and risky text.
# Points are scaled by confidence: a signal at the 0.75 threshold gives 34-38,
# so the model alone can raise a document to Yellow (review) but never to Red.
SEMANTIC_LABELS = {
    "threat": {
        "hypothesis": "someone threatening to harm or expose a person unless they pay",
        "label": "a threat or extortion",
        "points": 50,
    },
    "fraud": {
        "hypothesis": "a scam that tricks someone into paying money",
        "label": "fraud or a scam",
        "points": 45,
    },
    "credentials": {
        "hypothesis": "a request to send a password, PIN or OTP",
        "label": "a request for passwords or PINs",
        "points": 45,
    },
    "policy": {
        "hypothesis": "secretly hiding a transaction from auditors or finance",
        "label": "hiding transactions from auditors",
        "points": 45,
    },
}

CHUNK_WORDS = 60
MAX_CHUNKS = 8  # ~5 s on CPU for a long document
EVIDENCE_CHARS = 220

_classifier = None
_load_error: str | None = None
_load_lock = threading.Lock()
_inference_lock = threading.Lock()


def _load_classifier():
    global _classifier, _load_error

    if _classifier is not None or _load_error is not None:
        return _classifier

    with _load_lock:
        if _classifier is not None or _load_error is not None:
            return _classifier

        try:
            import torch
            from transformers import pipeline

            logger.info("Loading AI model %s (first run downloads it)", settings.SEMANTIC_MODEL_NAME)
            _classifier = pipeline(
                "zero-shot-classification",
                model=settings.SEMANTIC_MODEL_NAME,
                device=-1,
                # The weights are stored as float16, which is ~5x slower on a CPU.
                dtype=torch.float32,
            )
            logger.info("AI model ready")
        except Exception as error:  # missing packages, no internet on first run, ...
            _load_error = f"{type(error).__name__}: {error}"
            logger.warning("AI model unavailable, using rules only: %s", _load_error)

    return _classifier


def warm_up() -> None:
    """Load the model at server start so the first upload is not slow."""
    if settings.ENABLE_SEMANTIC_MODEL:
        _load_classifier()


def split_into_chunks(text: str) -> list[tuple[str, int, int]]:
    """Groups sentences into chunks of about CHUNK_WORDS words.
    Returns (chunk text, start offset, end offset) so evidence can be located."""
    chunks = []
    current_start = current_end = None
    current_words = 0

    for start, end in sentence_spans(text):
        words = len(text[start:end].split())

        if current_start is not None and current_words + words > CHUNK_WORDS:
            chunks.append((current_start, current_end))
            current_start, current_words = None, 0

        if current_start is None:
            current_start = start

        current_end = end
        current_words += words

    if current_start is not None:
        chunks.append((current_start, current_end))

    return [(" ".join(text[start:end].split()), start, end) for start, end in chunks[:MAX_CHUNKS]]


def _unavailable(status: str, reason: str) -> dict:
    return {"status": status, "model": settings.SEMANTIC_MODEL_NAME, "reason": reason, "signals": []}


def classify(text: str) -> dict:
    """Returns {"status", "model", "signals": [{key, label, confidence, evidence, points,
    start_index, end_index}]} — the offsets are the chunk the evidence came from.

    confidence is the label's share against all other labels, including
    "ordinary content". The caller decides which signals pass the threshold.

    One signal per label, with the highest confidence across all chunks.
    """
    if not settings.ENABLE_SEMANTIC_MODEL:
        return _unavailable("disabled", "Turned off in settings (ENABLE_SEMANTIC_MODEL).")

    chunks = split_into_chunks(text or "")

    if not chunks:
        return _unavailable("skipped", "No text to analyse.")

    classifier = _load_classifier()

    if classifier is None:
        return _unavailable("unavailable", _load_error or "Model not loaded.")

    chunk_texts = [chunk for chunk, _, _ in chunks]
    hypotheses = {config["hypothesis"]: key for key, config in SEMANTIC_LABELS.items()}
    hypotheses[NEUTRAL_HYPOTHESIS] = "neutral"

    try:
        with _inference_lock:
            results = classifier(
                chunk_texts,
                candidate_labels=list(hypotheses),
                hypothesis_template=HYPOTHESIS_TEMPLATE,
                multi_label=False,
            )
    except Exception as error:
        logger.exception("AI model failed on a document")
        return _unavailable("error", f"{type(error).__name__}: {error}")

    if isinstance(results, dict):
        results = [results]

    best: dict[str, dict] = {}

    for (_, chunk_start, chunk_end), result in zip(chunks, results):
        for hypothesis, confidence in zip(result["labels"], result["scores"]):
            key = hypotheses[hypothesis]

            if key == "neutral":
                continue

            if key not in best or confidence > best[key]["confidence"]:
                evidence = result["sequence"]
                best[key] = {
                    "confidence": round(float(confidence), 3),
                    "evidence": evidence if len(evidence) <= EVIDENCE_CHARS else evidence[:EVIDENCE_CHARS].rstrip() + "…",
                    "start_index": chunk_start,
                    "end_index": chunk_end,
                }

    signals = [
        {
            "key": key,
            "label": config["label"],
            "points": config["points"],
            **best[key],
        }
        for key, config in SEMANTIC_LABELS.items()
        if key in best
    ]

    return {"status": "ok", "model": settings.SEMANTIC_MODEL_NAME, "reason": "", "signals": signals}
