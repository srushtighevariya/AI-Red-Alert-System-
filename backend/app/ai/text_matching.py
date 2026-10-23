import re
from functools import lru_cache

# Python's \w does not include Indic vowel signs (e.g. Gujarati "ા"), so a plain
# \b boundary would split Gujarati words in the middle. Treat the Indic script
# blocks as word characters explicitly.
WORD_CHARS = r"\wऀ-෿"

# Common English endings, so "threaten" also finds "threatened" and "harm"
# finds "harmed" — but "harm" does not match inside "harmless" or "pharmacy".
ENGLISH_SUFFIXES = r"(?:s|es|d|ed|ing)?"

# Personal-data detectors: the first item of a type scores its full points,
# every further item of the same type adds this much (more records = more exposure).
REPEAT_ITEM_POINTS = 5


@lru_cache(maxsize=None)
def compile_phrase(phrase: str) -> re.Pattern:
    words = phrase.split()
    body = r"\s+".join(re.escape(word) for word in words)

    if phrase.isascii():
        pattern = rf"(?<![{WORD_CHARS}]){body}{ENGLISH_SUFFIXES}(?![{WORD_CHARS}])"
    else:
        # OCR often drops the small nasal marks (anusvara "ં", candrabindu "ઁ"),
        # e.g. "નહીં" is read as "નહી", so they are optional when matching.
        body = re.sub("[ઁં]", lambda mark: mark.group() + "?", body)
        # Gujarati attaches endings and postpositions directly to the word
        # ("ધમકી" -> "ધમકીઓ"), so only the start of the phrase is anchored.
        pattern = rf"(?<![{WORD_CHARS}]){body}"

    return re.compile(pattern, flags=re.IGNORECASE)


def find_phrase_positions(text: str, phrase: str) -> list[tuple[int, int]]:
    return [match.span() for match in compile_phrase(phrase).finditer(text)]


def spans_overlap(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < other_end and other_start < end for other_start, other_end in spans)


def score_items(items: list[dict], label_key: str) -> int:
    """Full points for the first item of each label, REPEAT_ITEM_POINTS for each repeat."""
    seen_labels = set()
    total = 0

    for item in items:
        label = item[label_key]

        if label in seen_labels:
            total += REPEAT_ITEM_POINTS
        else:
            seen_labels.add(label)
            total += item["risk_points"]

    return min(total, 100)
