import re

from app.ai.id_validators import is_valid_luhn
from app.ai.redaction import mask_value
from app.ai.text_matching import score_items, spans_overlap

# Indian ID numbers (Aadhaar, PAN, ...) are detected by indian_compliance_detector
# only, so the same number is never scored twice.
# Order matters: a later pattern skips text an earlier one already matched
# (a card number is not also reported as a phone number).
SENSITIVE_PATTERNS = {
    "email_address": {
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "risk_points": 15,
    },
    "credit_card_number": {
        "pattern": r"(?<![\d-])\d(?:[ -]?\d){12,18}(?!\d)",
        "risk_points": 40,
        "validate": is_valid_luhn,
    },
    "phone_number": {
        "pattern": r"(?<![\w+])(?:\+91[-\s]?)?[6-9]\d{4}[-\s]?\d{5}(?!\d)",
        "risk_points": 20,
    },
}


def detect_sensitive_information(text: str) -> dict:
    findings = []

    if not text:
        return {
            "sensitive_items_found": 0,
            "sensitive_risk_score": 0,
            "findings": [],
        }

    matched_spans = []

    for label, config in SENSITIVE_PATTERNS.items():
        validate = config.get("validate")

        for match in re.finditer(config["pattern"], text):
            raw_value = match.group()

            if validate and not validate(raw_value):
                continue

            if spans_overlap(match.start(), match.end(), matched_spans):
                continue

            matched_spans.append(match.span())
            findings.append(
                {
                    "type": label,
                    "masked_value": mask_value(raw_value),
                    "risk_points": config["risk_points"],
                    "start_index": match.start(),
                    "end_index": match.end(),
                }
            )

    findings.sort(key=lambda finding: finding["start_index"])

    return {
        "sensitive_items_found": len(findings),
        "sensitive_risk_score": score_items(findings, label_key="type"),
        "findings": findings,
    }
