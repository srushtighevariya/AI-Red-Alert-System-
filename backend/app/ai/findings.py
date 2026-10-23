"""One detailed, clickable list of everything the detectors found.

build_findings() turns the separate detector outputs into findings that each
carry their location (line, offsets), the masked sentence around them, why the
finding matters, what to do about it, and the points it contributes.

score_findings() recomputes the risk score from that list while leaving out
findings the user dismissed as "not a risk". With nothing dismissed it gives
exactly the score the pipeline computed (a test checks this).
"""

from app.ai.risk_scoring import get_alert_level
from app.ai.sentences import sentence_spans
from app.ai.text_matching import REPEAT_ITEM_POINTS

MAX_SEMANTIC_POINTS = 60
CONTEXT_MAX_CHARS = 320

CATEGORIES = {
    "threat": {"title": "Threat language", "scoring": "phrase", "cap": 100},
    "policy": {"title": "Policy violations", "scoring": "phrase", "cap": 100},
    "semantic": {"title": "AI model", "scoring": "sum", "cap": MAX_SEMANTIC_POINTS},
    "keyword": {"title": "Risky keywords", "scoring": "phrase", "cap": 100},
    "compliance": {"title": "Indian ID & banking data", "scoring": "items", "cap": 100},
    "sensitive": {"title": "Personal data", "scoring": "items", "cap": 100},
    "tampering": {"title": "Tampering signs", "scoring": "sum", "cap": 100},
    "anomaly": {"title": "Unusual patterns", "scoring": "sum", "cap": 100},
}

TYPE_LABELS = {
    "email_address": "Email address",
    "phone_number": "Phone number",
    "credit_card_number": "Card number",
    "aadhaar_number": "Aadhaar number",
    "pan_number": "PAN number",
    "gstin": "GSTIN",
    "ifsc_code": "IFSC code",
    "upi_id": "UPI ID",
    "bank_account_number": "Bank account number",
    "hidden_unicode_characters": "Hidden characters",
    "obfuscated_risky_words": "Disguised words",
    "ocr_corruption": "Unreadable characters",
    "unusual_spacing": "Unusual spacing",
    "duplicate_lines": "Repeated paragraph",
    "no_text_extracted": "No text found",
    "very_short_text": "Very short text",
    "excessive_uppercase": "Mostly capital letters",
    "high_digit_ratio": "Mostly numbers",
    "excessive_warning_symbols": "Repeated !!! or ???",
    "repeated_words": "Repeated words",
}

# (why it matters, what to do), by category or by "category:type".
GUIDANCE = {
    "threat": (
        "Threatening or extortion language is a strong sign of blackmail or coercion.",
        "Do not pay or reply. Keep the document as evidence and report it to your manager or the police.",
    ),
    "policy": (
        "Instructions to skip approvals, avoid audits or destroy records point to possible fraud or misconduct.",
        "Do not follow the instruction. Escalate to compliance or your manager.",
    ),
    "keyword": (
        "This word often appears in fraudulent, confidential or sensitive material.",
        "Read the sentence in context. It is often harmless, but check before sharing the document.",
    ),
    "sensitive:email_address": (
        "An email address is personal contact data and can be used for phishing.",
        "Fine on your own letterhead. Otherwise remove it before sharing the document outside your organisation.",
    ),
    "sensitive:phone_number": (
        "A mobile number lets anyone who gets this file contact, track or impersonate its owner.",
        "Remove or mask it before sharing outside your organisation.",
    ),
    "sensitive:credit_card_number": (
        "A valid card number (it passes the Luhn check) can be used for fraudulent payments.",
        "Never share it. Remove it from the document and ask the cardholder to contact their bank if it was exposed.",
    ),
    "compliance:aadhaar_number": (
        "Aadhaar numbers are protected identity data and are commonly misused for identity fraud.",
        "Use a masked Aadhaar (last 4 digits only) unless the full number is legally required.",
    ),
    "compliance:pan_number": (
        "A PAN identifies a taxpayer and is used in loan and KYC fraud.",
        "Share only with parties that legally need it.",
    ),
    "compliance:gstin": (
        "A GSTIN identifies a registered business. It is often public, but confirms who is involved.",
        "Usually fine on invoices. Verify it on the GST portal if the document asks you to pay.",
    ),
    "compliance:ifsc_code": (
        "Together with an account number, an IFSC code is enough to send money to an account.",
        "Before paying, confirm the bank details by phone with someone you already know.",
    ),
    "compliance:upi_id": (
        "A UPI ID can receive payments instantly, and changed UPI IDs are a common payment scam.",
        "Confirm the UPI ID with the recipient through a channel you already trust before paying.",
    ),
    "compliance:bank_account_number": (
        "Bank account numbers are financial data and are used in payment-diversion fraud.",
        "Check the account matches details you already have before sending money.",
    ),
    "semantic:threat": (
        "The AI model reads this passage as a threat or extortion, even without the usual keywords.",
        "Read the passage. If it pressures someone to pay or act, treat it like a threat.",
    ),
    "semantic:fraud": (
        "The AI model reads this passage as a scam or fraudulent request for money.",
        "Verify the request independently before paying anything.",
    ),
    "semantic:credentials": (
        "The AI model reads this passage as a request for passwords, PINs or OTPs.",
        "Never share passwords, PINs or OTPs. Genuine banks and companies do not ask for them.",
    ),
    "semantic:policy": (
        "The AI model reads this passage as hiding a transaction from auditors or finance.",
        "Escalate to compliance. Do not process the transaction until it has been approved properly.",
    ),
    "tampering": (
        "This can mean the text was edited to hide something or to slip past filters.",
        "Compare with the original document from the sender.",
    ),
    "tampering:duplicate_lines": (
        "A long sentence or paragraph appears more than once. Copy-paste edits sometimes leave duplicates.",
        "Usually harmless (repeated clauses or headers). Check that the repeated text was intended.",
    ),
    "anomaly": (
        "Unusual formatting is common in scam messages and in documents that were not read correctly.",
        "Look at the original. If the text was read badly, try a clearer scan.",
    ),
    "anomaly:no_text_extracted": (
        "No readable text was found, so nothing could be checked.",
        "Upload a clearer scan or a text-based PDF or Word file.",
    ),
}


def _guidance(category: str, finding_type: str) -> tuple[str, str]:
    return GUIDANCE.get(f"{category}:{finding_type}") or GUIDANCE[category]


def _context(text: str, spans: list[tuple[int, int]], start: int, end: int) -> tuple[str, int, int]:
    """The sentence around [start, end), whitespace-normalised, with the match
    offsets inside it. Long sentences are trimmed around the match."""
    sentence_start, sentence_end = start, end

    for span_start, span_end in spans:
        if span_start <= start < span_end:
            sentence_start, sentence_end = span_start, max(span_end, end)
            break

    trimmed_start = trimmed_end = False

    if sentence_end - sentence_start > CONTEXT_MAX_CHARS:
        room = max((CONTEXT_MAX_CHARS - (end - start)) // 2, 40)
        if start - room > sentence_start:
            cut = text.find(" ", start - room, start)  # start on a whole word
            sentence_start, trimmed_start = (cut + 1 if cut != -1 else start - room), True
        if end + room < sentence_end:
            cut = text.rfind(" ", end, end + room)  # end on a whole word
            sentence_end, trimmed_end = (cut if cut != -1 else end + room), True

    before = " ".join(text[sentence_start:start].split())
    match = " ".join(text[start:end].split())
    after = " ".join(text[end:sentence_end].split())

    prefix = ("…" if trimmed_start else "") + before
    if before and text[start - 1].isspace():
        prefix += " "

    suffix = (" " if after and text[end:end + 1].isspace() else "") + after + ("…" if trimmed_end else "")

    return prefix + match + suffix, len(prefix), len(prefix) + len(match)


def build_findings(analysis: dict, redacted_text: str) -> list[dict]:
    spans = sentence_spans(redacted_text)
    raw = []

    def add(category, finding_type, label, value, base_points, start=None, end=None, **extra):
        raw.append(
            {
                "category": category,
                "type": finding_type,
                "label": label,
                "value": value,
                "base_points": base_points,
                "start_index": start,
                "end_index": end,
                **extra,
            }
        )

    for item in analysis["threat_analysis"]["threats"]:
        add("threat", item["phrase"], f"“{item['phrase']}”", item["phrase"], item["risk_points"], item["start_index"], item["end_index"])

    for item in analysis["policy_violation_analysis"]["violations"]:
        add("policy", item["phrase"], f"“{item['phrase']}”", item["phrase"], item["risk_points"], item["start_index"], item["end_index"])

    for item in analysis["keyword_analysis"]["highlighted_sections"]:
        add("keyword", item["keyword"], f"“{item['keyword']}”", item["keyword"], item["risk_points"], item["start_index"], item["end_index"])

    for category, key in (("sensitive", "sensitive_info_analysis"), ("compliance", "indian_compliance_analysis")):
        for item in analysis[key]["findings"]:
            add(category, item["type"], TYPE_LABELS.get(item["type"], item["type"]), item["masked_value"],
                item["risk_points"], item["start_index"], item["end_index"])

    for item in analysis.get("semantic_analysis", {}).get("signals", []):
        note = "Already counted by the rules, so it adds no extra points." if item["already_found_by_rules"] else ""
        add("semantic", item["key"], f"Reads as {item['label']}", item["evidence"], item["points"],
            item.get("start_index"), item.get("end_index"), confidence=item["confidence"], note=note)

    for item in analysis["tampering_analysis"]["findings"]:
        add("tampering", item["type"], TYPE_LABELS.get(item["type"], item["type"]), item["description"], item["risk_points"])

    for item in analysis["anomaly_analysis"]["anomalies"]:
        add("anomaly", item["type"], TYPE_LABELS.get(item["type"], item["type"]), item["description"], item["risk_points"])

    order = list(CATEGORIES)
    raw.sort(key=lambda f: (order.index(f["category"]), f["start_index"] if f["start_index"] is not None else 10**12))

    findings = []
    counters = {}

    for finding in raw:
        category = finding["category"]
        counters[category] = counters.get(category, 0) + 1
        why, what_to_do = _guidance(category, finding["type"])
        finding.setdefault("note", "")
        finding.setdefault("confidence", None)
        finding.update(id=f"{category}-{counters[category]}", why=why, what_to_do=what_to_do,
                       line=None, context="", context_match_start=None, context_match_end=None)

        if finding["start_index"] is not None:
            start, end = finding["start_index"], finding["end_index"]
            finding["line"] = redacted_text.count("\n", 0, start) + 1
            context, match_start, match_end = _context(redacted_text, spans, start, end)
            finding.update(context=context, context_match_start=match_start, context_match_end=match_end)

        findings.append(finding)

    scores = score_findings(findings)
    for finding in findings:
        finding["points"] = scores["effective_points"][finding["id"]]

    return findings


def score_findings(findings: list[dict], dismissed: set[str] | frozenset = frozenset()) -> dict:
    """Risk score from the findings, leaving out dismissed ones.

    phrase: each distinct phrase counts once (repeats add nothing).
    items:  first item of a type counts fully, each repeat adds REPEAT_ITEM_POINTS.
    sum:    every finding adds its points.
    Each category is capped, and the total is capped at 100.
    """
    effective = {}
    category_scores = {}

    for category, config in CATEGORIES.items():
        seen = set()
        total = 0

        for finding in findings:
            if finding["category"] != category:
                continue

            if finding["id"] in dismissed:
                effective[finding["id"]] = 0
                continue

            points = finding["base_points"]

            if config["scoring"] == "phrase" and finding["type"] in seen:
                points = 0
            elif config["scoring"] == "items" and finding["type"] in seen:
                points = REPEAT_ITEM_POINTS

            seen.add(finding["type"])
            effective[finding["id"]] = points
            total += points

        category_scores[category] = min(total, config["cap"])

    risk_score = min(sum(category_scores.values()), 100)

    return {
        "effective_points": effective,
        "category_scores": category_scores,
        "risk_score": risk_score,
        "trust_score": 100 - risk_score,
        "alert_level": get_alert_level(risk_score),
    }
