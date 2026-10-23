import re


def detect_abnormal_patterns(text: str) -> dict:
    anomalies = []
    total_risk_score = 0

    if not text:
        return {
            "anomalies_found": 1,
            "anomaly_risk_score": 20,
            "anomalies": [
                {
                    "type": "no_text_extracted",
                    "description": "No readable text was extracted from the document.",
                    "risk_points": 20,
                }
            ],
        }

    word_count = len(text.split())
    letter_count = sum(1 for char in text if char.isalpha())
    uppercase_count = sum(1 for char in text if char.isupper())
    digit_count = sum(1 for char in text if char.isdigit())
    exclamation_count = text.count("!")
    # Runs like "!!!" or "?!?". Single question marks are normal (FAQs, forms).
    has_repeated_symbols = re.search(r"[!?]{3,}", text) is not None

    if word_count < 5:
        anomalies.append(
            {
                "type": "very_short_text",
                "description": "Extracted text is very short, which may indicate incomplete extraction.",
                "risk_points": 10,
            }
        )
        total_risk_score += 10

    if letter_count > 40 and uppercase_count / letter_count > 0.6:
        anomalies.append(
            {
                "type": "excessive_uppercase",
                "description": "Large amount of uppercase text detected.",
                "risk_points": 15,
            }
        )
        total_risk_score += 15

    if len(text) > 50 and digit_count / len(text) > 0.25:
        anomalies.append(
            {
                "type": "high_digit_ratio",
                "description": "Document contains an unusually high number of digits.",
                "risk_points": 15,
            }
        )
        total_risk_score += 15

    if has_repeated_symbols or exclamation_count > 5:
        anomalies.append(
            {
                "type": "excessive_warning_symbols",
                "description": "Repeated exclamation or question marks detected.",
                "risk_points": 10,
            }
        )
        total_risk_score += 10

    repeated_word_pattern = r"\b(\w+)(?:\s+\1){3,}\b"
    if re.search(repeated_word_pattern, text, flags=re.IGNORECASE):
        anomalies.append(
            {
                "type": "repeated_words",
                "description": "Same word repeated many times in sequence.",
                "risk_points": 15,
            }
        )
        total_risk_score += 15

    total_risk_score = min(total_risk_score, 100)

    return {
        "anomalies_found": len(anomalies),
        "anomaly_risk_score": total_risk_score,
        "anomalies": anomalies,
    }