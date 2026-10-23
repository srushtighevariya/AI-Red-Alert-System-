import re

from app.ai.id_validators import is_valid_aadhaar
from app.ai.redaction import mask_value
from app.ai.text_matching import score_items, spans_overlap

# A bare 9-18 digit number is usually an order or invoice number, so it only
# counts as a bank account when one of these appears just before it.
BANK_ACCOUNT_CONTEXT = ("account", "a/c", "acct", "acc no", "ખાતા", "ખાતું")
BANK_ACCOUNT_CONTEXT_WINDOW = 40


def has_bank_account_context(text: str, start: int) -> bool:
    preceding_text = text[max(start - BANK_ACCOUNT_CONTEXT_WINDOW, 0):start].lower()

    return any(word in preceding_text for word in BANK_ACCOUNT_CONTEXT)


# Order matters: a later pattern skips text an earlier one already matched
# (the PAN inside a GSTIN, or an Aadhaar number, is not also a bank account).
INDIAN_COMPLIANCE_PATTERNS = {
    "gstin": {
        "pattern": r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b",
        "risk_points": 35,
    },
    "pan_number": {
        "pattern": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        "risk_points": 35,
    },
    "aadhaar_number": {
        "pattern": r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)",
        "risk_points": 35,
        "validate": lambda text, match: is_valid_aadhaar(match.group()),
    },
    "ifsc_code": {
        "pattern": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
        "risk_points": 25,
    },
    "upi_id": {
        # The handle after "@" has no dot, which keeps email addresses out.
        "pattern": r"(?<![\w.-])[A-Za-z0-9._-]{2,256}@[A-Za-z]{2,64}(?![\w-]|\.[A-Za-z0-9])",
        "risk_points": 25,
    },
    "bank_account_number": {
        "pattern": r"(?<!\d)\d{9,18}(?!\d)",
        "risk_points": 25,
        "validate": lambda text, match: has_bank_account_context(text, match.start()),
    },
}


def detect_indian_compliance_data(
    text: str,
    exclude_spans: list[tuple[int, int]] | None = None,
) -> dict:
    """exclude_spans: text already reported by another detector (e.g. a phone number)."""
    findings = []

    if not text:
        return {
            "compliance_items_found": 0,
            "compliance_risk_score": 0,
            "findings": [],
        }

    matched_spans = list(exclude_spans or [])

    for label, config in INDIAN_COMPLIANCE_PATTERNS.items():
        validate = config.get("validate")

        for match in re.finditer(config["pattern"], text):
            if validate and not validate(text, match):
                continue

            if spans_overlap(match.start(), match.end(), matched_spans):
                continue

            matched_spans.append(match.span())
            findings.append(
                {
                    "type": label,
                    "masked_value": mask_value(match.group()),
                    "risk_points": config["risk_points"],
                    "start_index": match.start(),
                    "end_index": match.end(),
                }
            )

    findings.sort(key=lambda finding: finding["start_index"])

    return {
        "compliance_items_found": len(findings),
        "compliance_risk_score": score_items(findings, label_key="type"),
        "findings": findings,
    }
