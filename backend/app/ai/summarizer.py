"""Document summaries.

key sentences — extractive TextRank: sentences are ranked by how strongly they
    share words with the rest of the document, and the top ones are returned in
    their original order. Language-independent, so it works for Gujarati too.
risk summary — one plain-language paragraph describing what the detectors found.
"""

import math
import re

from app.ai.sentences import split_sentences

# Headings and address lines are short; prefer real sentences for the summary.
MIN_SUMMARY_SENTENCE_WORDS = 6
WORD =re.compile(r"[\w઀-૿]+")

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for", "from",
    "has", "have", "he", "her", "his", "i", "in", "is", "it", "its", "of", "on",
    "or", "our", "she", "that", "the", "their", "them", "they", "this", "to",
    "was", "we", "were", "will", "with", "you", "your", "not", "do", "can",
    "છે", "અને", "આ", "તે", "માં", "ના", "ની", "નું", "નો", "પણ", "કે",
}

DAMPING = 0.85
ITERATIONS = 30
MAX_SENTENCE_CHARS = 400


def split_into_sentences(text: str) -> list[str]:
    return [sentence for sentence in split_sentences(text) if len(WORD.findall(sentence)) >= 3]


def _content_words(sentence: str) -> set[str]:
    return {word for word in WORD.findall(sentence.lower()) if word not in STOPWORDS and len(word) > 1}


def _similarity(words_a: set[str], words_b: set[str]) -> float:
    if len(words_a) < 2 or len(words_b) < 2:
        return 0.0

    shared = len(words_a & words_b)
    return shared / (math.log(len(words_a)) + math.log(len(words_b)))


def rank_sentences(sentences: list[str]) -> list[float]:
    words = [_content_words(sentence) for sentence in sentences]
    count = len(sentences)
    weights = [[_similarity(words[i], words[j]) if i != j else 0.0 for j in range(count)] for i in range(count)]
    out_totals = [sum(row) for row in weights]
    scores = [1.0] * count

    for _ in range(ITERATIONS):
        scores = [
            (1 - DAMPING)
            + DAMPING * sum(weights[j][i] / out_totals[j] * scores[j] for j in range(count) if out_totals[j])
            for i in range(count)
        ]

    return scores


def generate_basic_summary(text: str, max_sentences: int | None = None) -> dict:
    if not text or not text.strip():
        return {
            "summary_text": "No text was extracted from the document.",
            "key_sentences": [],
            "word_count": 0,
            "sentence_count": 0,
        }

    sentences = split_into_sentences(text)
    word_count = len(text.split())

    if max_sentences is None:
        max_sentences = 2 if len(sentences) <= 8 else 3

    full_sentences = [
        sentence for sentence in sentences if len(WORD.findall(sentence)) >= MIN_SUMMARY_SENTENCE_WORDS
    ]
    candidates = full_sentences if len(full_sentences) >= max_sentences else sentences

    if len(candidates) <= max_sentences:
        key_sentences = candidates or [" ".join(text.split())]
    else:
        scores = rank_sentences(candidates)
        top = sorted(range(len(candidates)), key=lambda index: scores[index], reverse=True)[:max_sentences]
        key_sentences = [candidates[index] for index in sorted(top)]

    key_sentences = [
        sentence if len(sentence) <= MAX_SENTENCE_CHARS else sentence[:MAX_SENTENCE_CHARS].rstrip() + "…"
        for sentence in key_sentences
    ]

    return {
        "summary_text": " ".join(key_sentences),
        "key_sentences": key_sentences,
        "word_count": word_count,
        "sentence_count": len(sentences),
    }


def _quote_list(values: list[str], limit: int = 3) -> str:
    unique = list(dict.fromkeys(values))
    shown = ", ".join(f'"{value}"' for value in unique[:limit])
    return shown + (f" and {len(unique) - limit} more" if len(unique) > limit else "")


def _type_list(findings: list[dict]) -> str:
    names = [finding["type"].replace("_", " ") for finding in findings]
    unique = list(dict.fromkeys(names))
    return ", ".join(unique)


def generate_risk_summary(analysis: dict) -> str:
    """One paragraph, in plain language, of what the detectors found."""
    risk = analysis["risk_analysis"]
    parts = []

    threats = [item["phrase"] for item in analysis["threat_analysis"]["threats"]]
    if threats:
        parts.append(f"threatening language ({_quote_list(threats)})")

    violations = [item["phrase"] for item in analysis["policy_violation_analysis"]["violations"]]
    if violations:
        parts.append(f"instructions to bypass policy ({_quote_list(violations)})")

    keywords = analysis["keyword_analysis"]["matched_keywords"]
    if keywords:
        parts.append(f"risky keywords ({_quote_list(keywords)})")

    personal = analysis["sensitive_info_analysis"]["findings"]
    if personal:
        parts.append(f"{len(personal)} personal data item(s) ({_type_list(personal)})")

    compliance = analysis["indian_compliance_analysis"]["findings"]
    if compliance:
        parts.append(f"{len(compliance)} Indian ID or banking item(s) ({_type_list(compliance)})")

    semantic = [item["label"] for item in analysis.get("semantic_analysis", {}).get("signals", []) if item.get("counted")]
    if semantic:
        parts.append(f"content the AI model reads as {', '.join(dict.fromkeys(semantic))}")

    tampering = analysis["tampering_analysis"]["findings"]
    if tampering:
        parts.append("signs of tampering")

    level = risk["alert_level"]
    opening = f"{level} alert with a risk score of {risk['risk_score']}/100."

    if not parts:
        return f"{opening} No threats, policy violations or personal data were found."

    if len(parts) == 1:
        found = parts[0]
    else:
        found = ", ".join(parts[:-1]) + " and " + parts[-1]

    return f"{opening} The document contains {found}."
