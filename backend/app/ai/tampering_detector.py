import re

MIN_DUPLICATE_LINE_WORDS = 8


def detect_tampering_suspicion(text: str) -> dict:
    findings = []
    total_score = 0

    def add_finding(finding_type: str, description: str, points: int) -> None:
        nonlocal total_score

        findings.append(
            {
                "type": finding_type,
                "description": description,
                "risk_points": points,
            }
        )
        total_score += points

    if not text:
        return {
            "tampering_suspicions_found": 0,
            "tampering_risk_score": 0,
            "findings": [],
        }

    if re.search(r"[\u200B-\u200D\uFEFF]", text):
        add_finding(
            "hidden_unicode_characters",
            "Invisible Unicode characters were detected.",
            30,
        )

    # Only the substituted spellings: the plain words are scored by keyword_detector.
    # (\b would not work before "@", so lookarounds are used instead.)
    obfuscated_pattern = r"(?<!\w)(passw0rd|pa55word|p@ssword|p@ssw0rd|acc0unt|fr@ud|fr4ud)(?!\w)"
    if re.search(obfuscated_pattern, text, flags=re.IGNORECASE):
        add_finding(
            "obfuscated_risky_words",
            "Possible character substitution was detected.",
            25,
        )

    if "\ufffd" in text:
        add_finding(
            "ocr_corruption",
            "Unreadable replacement characters were detected.",
            15,
        )

    if re.search(r"[ \t]{5,}", text):
        add_finding(
            "unusual_spacing",
            "Unusually large spaces were detected.",
            10,
        )

    # Only long lines count: short repeats are page headers and footers,
    # which every multi-page PDF has.
    lines = [
        line.strip().lower()
        for line in text.splitlines()
        if len(line.split()) >= MIN_DUPLICATE_LINE_WORDS
    ]
    if len(lines) != len(set(lines)):
        add_finding(
            "duplicate_lines",
            "Duplicate sentences or paragraphs were detected.",
            15,
        )

    return {
        "tampering_suspicions_found": len(findings),
        "tampering_risk_score": min(total_score, 100),
        "findings": findings,
    }